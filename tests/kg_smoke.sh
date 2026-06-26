#!/bin/bash
# KG completeness smoke test — the gate that turns "KG is incomplete" from a
# production surprise into a failed check.
#
# Asserts, against a running platform:
#   1. /tvbo/api/kg/health verdict == KG_OK (every ground-truth category fully
#      ingested — catches the partial-ingest failures a bare dynamics>0 misses).
#   2. tvbo-api parity: the Odoo KG serves at least as many records as the
#      stateless tvbo-api for the categories tvbo-api exposes (dynamics, networks,
#      experiments). The KG materializes the same ground truth; it must not lose
#      records relative to the YAML-reading API.
#
# Usage:
#   tests/kg_smoke.sh                      # localhost:8169 (KG) + :8001 (tvbo-api)
#   KG_URL=http://host:8069 API_URL=http://host:8000 tests/kg_smoke.sh
# Exit 0 = pass; non-zero = fail (use in CI before/after deploy).
set -uo pipefail

KG_URL="${KG_URL:-http://localhost:8169}"
API_URL="${API_URL:-http://localhost:8001}"
FAIL=0

say()  { printf '%s\n' "$*"; }
pass() { printf '  ✓ %s\n' "$*"; }
warn() { printf '  ~ %s\n' "$*"; }   # non-fatal
fail() { printf '  ✗ %s\n' "$*"; FAIL=1; }

# Read a count via $1($2), retrying to ride out transient unavailability.
# Echoes the value; returns non-zero if still unreadable after retries.
retry_count() {
  local fn="$1" arg="$2" v="" i
  for i in 1 2 3; do
    v=$("$fn" "$arg")
    [ -n "$v" ] && [ "$v" != "-1" ] && { printf '%s' "$v"; return 0; }
    sleep 2
  done
  printf '%s' "$v"; return 1
}

say "== KG completeness smoke =="
say "KG_URL=$KG_URL  API_URL=$API_URL"

# ---- 1. health verdict + per-category completeness -------------------------
HEALTH=$(curl -sS --max-time 30 "$KG_URL/tvbo/api/kg/health" 2>/dev/null)
if [ -z "$HEALTH" ]; then
  fail "no response from $KG_URL/tvbo/api/kg/health"
  exit 1
fi

VERDICT=$(printf '%s' "$HEALTH" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("verdict","?"))' 2>/dev/null)
say ""
say "[1] /kg/health verdict: ${VERDICT:-unparseable}"
if [ "$VERDICT" = "KG_OK" ]; then
  pass "verdict KG_OK"
else
  SHORT=$(printf '%s' "$HEALTH" | python3 -c 'import sys,json;print(", ".join(json.load(sys.stdin).get("shortfalls") or []))' 2>/dev/null)
  fail "verdict='${VERDICT:-unparseable}' (expected KG_OK); shortfalls: ${SHORT:-?}"
fi

# Per-category expected vs actual (so a shortfall names the culprit)
printf '%s' "$HEALTH" | python3 -c '
import sys, json
d = json.load(sys.stdin)
for cat, c in sorted((d.get("completeness") or {}).items()):
    mark = "ok " if c.get("ok") else "SHORT"
    print(f"      {mark}  {cat}: {c.get(\"actual\")}/{c.get(\"expected\")}")
unc = d.get("uncovered_categories") or []
if unc:
    print("      UNCOVERED registry categories (records the KG can never show):",
          ", ".join(u.get("category","?") for u in unc))
' 2>/dev/null || true

# ---- 2. tvbo-api parity ----------------------------------------------------
say ""
say "[2] tvbo-api parity (KG must serve >= tvbo-api per category)"
count_api() { curl -sS --max-time 30 "$API_URL/api/v1/$1" 2>/dev/null \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d) if isinstance(d,list) else len(d.get("items",[])))' 2>/dev/null; }
count_kg()  { curl -sS --max-time 30 "$KG_URL/tvbo/api/kg/data?entity=$1" 2>/dev/null \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(len(d) if isinstance(d,list) else -1)' 2>/dev/null; }

# (tvbo-api endpoint, KG entity)
for pair in "dynamics:dynamics" "networks:network" "experiments:experiment"; do
  api_ep="${pair%%:*}"; kg_ep="${pair##*:}"
  # KG side is what we gate — unreadable KG is a hard failure.
  k=$(retry_count count_kg "$kg_ep") || { fail "parity $kg_ep: KG /data unreadable"; continue; }
  # tvbo-api is the cross-check — if it's transiently down, /kg/health already
  # gated completeness, so warn (don't fail the gate on the api's availability).
  a=$(retry_count count_api "$api_ep") || {
    warn "parity $kg_ep: tvbo-api /$api_ep unreadable after retries (skipped; /kg/health is authoritative)"; continue; }
  if [ "$k" -ge "$a" ]; then
    pass "parity $kg_ep: KG $k >= tvbo-api $a"
  else
    fail "parity $kg_ep: KG $k < tvbo-api $a (KG is missing records)"
  fi
done

say ""
if [ "$FAIL" -eq 0 ]; then say "RESULT: PASS"; else say "RESULT: FAIL"; fi
exit "$FAIL"
