#!/bin/bash
# End-to-end auth + sharing smoke for the platform REST API (controllers/api.py).
#
# Proves the security-critical contract that had ZERO end-to-end coverage:
#   • no Bearer key            -> 401
#   • a user sees their own PRIVATE experiment + SHARED + public ground truth
#   • another user sees the SHARED one but NEVER the owner's PRIVATE (list + 404)
#   • a push (save from Python) requires a key, creates the record, round-trips
#
# Setup (users, API keys, two owned experiments) is done server-side via
# `odoo shell`; the assertions run as a plain HTTP client with Bearer tokens —
# exactly how the tvbo Python client talks to the platform.
#
# Usage:  tests/api_auth_smoke.sh
#         BASE=http://host:8069 DB=tvbo_dev DOCKER=tvbo-odoo-dev tests/api_auth_smoke.sh
set -uo pipefail

BASE="${BASE:-http://localhost:8169}"
DB="${DB:-tvbo_dev}"
DOCKER="${DOCKER:-tvbo-odoo-dev}"
DB_HOST="${DB_HOST:-postgres}"; DB_USER="${DB_USER:-odoo}"; DB_PASSWORD="${DB_PASSWORD:-odoo}"
FAIL=0
pass() { printf '  ✓ %s\n' "$*"; }
fail() { printf '  ✗ %s\n' "$*"; FAIL=1; }

# ---- server-side setup: users + keys + a private and a shared experiment ----
SETUP=$(docker exec -i "$DOCKER" odoo shell -d "$DB" \
  --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" --log-level=error <<'PY' 2>/dev/null
import logging; logging.disable(logging.NOTSET)
U=env['res.users'].sudo(); K=env['tvbo.api_key'].sudo()
S=env['tvbo.model_share'].sudo(); E=env['tvbo.simulation_experiment'].sudo()
def user(login,name):
    u=U.search([('login','=',login)],limit=1)
    return u or U.create({'login':login,'name':name,'email':login})
owner=user('e2e_owner@test.local','E2E Owner'); other=user('e2e_other@test.local','E2E Other')
# clean prior test state (idempotent re-runs)
old=E.search([('label','in',['E2E-Private-Test','E2E-Shared-Test'])])
S.search([('experiment_id','in',old.ids)]).unlink(); old.unlink()
K.search([('user_id','in',(owner+other).ids),('name','=','e2e-test')]).unlink()
# a public (share-less, ground-truth) experiment to clone
shared=S.search([('experiment_id','!=',False)]).mapped('experiment_id').ids
src=E.search([('id','not in',shared)] if shared else [],limit=1)
priv=src.copy({'label':'E2E-Private-Test'}); shar=src.copy({'label':'E2E-Shared-Test'})
S.create({'experiment_id':priv.id,'owner_user_id':owner.id,'visibility':'private'})
S.create({'experiment_id':shar.id,'owner_user_id':owner.id,'visibility':'shared'})
_,ok=K.generate('e2e-test',user=owner); _,otk=K.generate('e2e-test',user=other)
env.cr.commit()
print(f"OWNER_KEY={ok}"); print(f"OTHER_KEY={otk}")
print(f"PRIV_ID={priv.id}"); print(f"SHAR_ID={shar.id}"); print(f"SRC_ID={src.id}")
PY
)
eval "$(printf '%s\n' "$SETUP" | grep -E '^(OWNER_KEY|OTHER_KEY|PRIV_ID|SHAR_ID|SRC_ID)=')"
if [ -z "${OWNER_KEY:-}" ] || [ -z "${PRIV_ID:-}" ]; then
  echo "SETUP FAILED:"; printf '%s\n' "$SETUP" | tail -15; exit 2
fi
echo "== API auth/sharing smoke =="
echo "BASE=$BASE  owner_key=${OWNER_KEY:0:12}…  private_exp=$PRIV_ID  shared_exp=$SHAR_ID"

EXP="$BASE/api/tvbo/v1/experiments"
code()  { curl -s -o /dev/null -w '%{http_code}' "$@"; }
ids()   { curl -s "$@" | python3 -c 'import sys,json;print(*[e["id"] for e in (json.load(sys.stdin).get("data") or [])])' 2>/dev/null; }
has()   { printf ' %s ' "$1" | grep -q " $2 "; }

# ---- 1. unauthenticated is rejected ----------------------------------------
echo ""; echo "[1] auth required"
[ "$(code "$EXP")" = "401" ] && pass "GET list without key -> 401" || fail "GET list without key not 401"
[ "$(code -X POST "$EXP")" = "401" ] && pass "POST without key -> 401" || fail "POST without key not 401"
[ "$(code -H "Authorization: Bearer tvbo_boguskey" "$EXP")" = "401" ] && pass "bogus key -> 401" || fail "bogus key not 401"

# ---- 2. visibility on the list endpoint ------------------------------------
echo ""; echo "[2] list visibility"
OWN=$(ids -H "Authorization: Bearer $OWNER_KEY" "$EXP")
OTH=$(ids -H "Authorization: Bearer $OTHER_KEY" "$EXP")
has "$OWN" "$PRIV_ID" && pass "owner sees own PRIVATE ($PRIV_ID)" || fail "owner missing own PRIVATE ($PRIV_ID)"
has "$OWN" "$SHAR_ID" && pass "owner sees SHARED ($SHAR_ID)"      || fail "owner missing SHARED ($SHAR_ID)"
has "$OTH" "$SHAR_ID" && pass "other sees SHARED ($SHAR_ID)"      || fail "other missing SHARED ($SHAR_ID)"
has "$OTH" "$PRIV_ID" && fail "LEAK: other sees owner's PRIVATE ($PRIV_ID)" || pass "other does NOT see owner's PRIVATE"

# ---- 3. visibility on the detail endpoint ----------------------------------
echo ""; echo "[3] detail visibility"
[ "$(code -H "Authorization: Bearer $OWNER_KEY" "$EXP/$PRIV_ID")" = "200" ] && pass "owner GET own PRIVATE detail -> 200 (round-trip)" || fail "owner cannot read own PRIVATE detail"
[ "$(code -H "Authorization: Bearer $OTHER_KEY" "$EXP/$PRIV_ID")" = "404" ] && pass "other GET owner's PRIVATE detail -> 404" || fail "LEAK: other can read owner's PRIVATE detail"
[ "$(code -H "Authorization: Bearer $OTHER_KEY" "$EXP/$SHAR_ID")" = "200" ] && pass "other GET SHARED detail -> 200" || fail "other cannot read SHARED detail"

# ---- 4. push (save from Python) round-trips --------------------------------
echo ""; echo "[4] push round-trip"
curl -s -H "Authorization: Bearer $OWNER_KEY" "$EXP/$SRC_ID?format=yaml" -o /tmp/e2e_src.yaml
PUSH=$(curl -s -H "Authorization: Bearer $OWNER_KEY" -H "Content-Type: application/x-yaml" \
  --data-binary @/tmp/e2e_src.yaml "$EXP?visibility=private")
NEW_ID=$(printf '%s' "$PUSH" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
if [ -n "$NEW_ID" ]; then
  pass "owner pushed experiment -> id=$NEW_ID"
  [ "$(code -H "Authorization: Bearer $OWNER_KEY" "$EXP/$NEW_ID")" = "200" ] && pass "pushed experiment readable by owner" || fail "pushed experiment not readable"
  [ "$(code -H "Authorization: Bearer $OTHER_KEY" "$EXP/$NEW_ID")" = "404" ] && pass "pushed experiment private to other -> 404" || fail "LEAK: pushed private experiment visible to other"
else
  fail "push did not return an id: $(printf '%s' "$PUSH" | head -c 200)"
fi

echo ""
[ "$FAIL" -eq 0 ] && { echo "RESULT: PASS"; exit 0; } || { echo "RESULT: FAIL"; exit 1; }
