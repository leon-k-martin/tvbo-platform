#!/bin/bash
set -euo pipefail

# Ensure Python exceptions are visible (no output buffering)
export PYTHONUNBUFFERED=1

# Logging helper
log() {
  echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $*"
}

# Run odoo commands with error capture (set -e would hide the traceback).
# Mirror output to /var/lib/odoo/upgrade.log so it survives container restart.
UPGRADE_LOG=/var/lib/odoo/upgrade.log

# Report an odoo failure: dump context, optionally hold the pod for debugging,
# then exit. Split out so a caller that can self-heal (see the upgrade block) may
# attempt recovery before deciding the failure is terminal.
handle_odoo_failure() {
  local rc="$1"; shift
  log "ERROR: odoo command failed with exit code $rc" | tee -a "$UPGRADE_LOG"
  log "Command was: odoo $*" | tee -a "$UPGRADE_LOG"
  log "Last 50 lines of upgrade log:" | tee -a "$UPGRADE_LOG"
  tail -50 "$UPGRADE_LOG" || true
  if [ "$rc" -eq 137 ] || [ "$rc" -eq 255 ]; then
    log "Checking dmesg for OOM..."
    dmesg 2>/dev/null | tail -20 || true
  fi
  if [ "${TVBO_KEEP_ALIVE_ON_FAIL:-0}" = "1" ]; then
    log "TVBO_KEEP_ALIVE_ON_FAIL=1 set; sleeping forever for kubectl exec debugging"
    sleep infinity
  fi
  exit "$rc"
}

# Run odoo, tee output to the persistent log, and RETURN its exit code without
# exiting. ODOO_LOG_LEVEL, when set, overrides the per-command --log-level; when
# unset each caller's explicit --log-level applies (no forced debug default —
# that was making "info" upgrades emit full DEBUG output).
run_odoo_soft() {
  set +e
  odoo "$@" ${ODOO_LOG_LEVEL:+--log-level="$ODOO_LOG_LEVEL"} 2>&1 | tee -a "$UPGRADE_LOG"
  local rc=${PIPESTATUS[0]}
  set -e
  return "$rc"
}

# Run odoo; on failure report + (optionally hold) + exit. For steps that have
# nothing to recover.
run_odoo() {
  local rc=0
  run_odoo_soft "$@" || rc=$?
  [ "$rc" -eq 0 ] || handle_odoo_failure "$rc" "$*"
}

# Self-heal the known "stale Many2many _rel table" upgrade abort. When a slot's
# m2m relation is regenerated with different join columns, the old _rel table
# survives and Odoo aborts adding the FK on a column that no longer exists:
#   bad query: ... ALTER TABLE "<rel>" ADD FOREIGN KEY ("<col>") ...
#   ERROR: column "<col>" referenced in foreign key constraint does not exist
# reconcile_schema's m2m pass should catch this from the model source, but it
# can miss inherited/relation-less m2m. As a backstop we pull the offending
# table straight from the failed upgrade log and drop it (Odoo recreates it with
# the right columns; link rows are repopulated on ingest). Only *_rel tables are
# ever dropped, never a real entity table. Returns 0 iff something was dropped.
drop_stale_m2m_from_log() {
  local logfile="$1" tables t dropped=0
  tables=$(grep -B1 'referenced in foreign key constraint does not exist' "$logfile" 2>/dev/null \
    | grep -oE 'ALTER TABLE "[a-z0-9_]+_rel"' \
    | sed -E 's/.*"([a-z0-9_]+)".*/\1/' | sort -u) || true
  [ -n "$tables" ] || return 1
  for t in $tables; do
    log "↻ m2m self-heal: dropping stale relation table '$t' (Odoo will recreate it)"
    if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -c "DROP TABLE IF EXISTS \"$t\" CASCADE;" >> "$UPGRADE_LOG" 2>&1; then
      dropped=1
    else
      log "⚠ m2m self-heal: failed to drop '$t'"
    fi
  done
  [ "$dropped" = "1" ]
}

# Version-independent schema reconciler (scripts/reconcile_schema.py).
#   $1 = phase: "pre"  (before -u tvbo) renames/stashes/drops conflicting columns;
#               "post" (after  -u tvbo) re-links stashed enum text to FK ids.
# Bridges schema shape changes that arrive on a follow-latest rebuild without a
# module version bump (Odoo's version-gated migrations would not run for those).
# Non-fatal: on failure we log and continue, which is no worse than skipping it.
reconcile_schema() {
  local phase="$1"
  local recon="${TVBO_RECONCILE_PY:-/opt/tvbo/reconcile_schema.py}"
  local models_dir="/mnt/extra-addons/tvbo/models"
  if [ ! -f "$recon" ]; then
    log "⚠ reconcile_schema.py not found at $recon; skipping $phase bridges"
    return 0
  fi
  log "Schema reconcile ($phase)..."
  set +e
  python3 "$recon" --phase "$phase" \
    --db-host "$DB_HOST" --db-user "$DB_USER" --db-password "$DB_PASSWORD" \
    --db-name "$DB_NAME" --models-dir "$models_dir" 2>&1 | tee -a "$UPGRADE_LOG"
  local rc=${PIPESTATUS[0]}
  set -e
  if [ "$rc" -ne 0 ]; then
    log "⚠ schema reconcile ($phase) exited $rc (non-fatal); continuing"
  else
    log "✓ schema reconcile ($phase) complete"
  fi
}

# Rotate upgrade log: keep previous as .prev so it survives container restart
mkdir -p "$(dirname "$UPGRADE_LOG")"
if [ -f "$UPGRADE_LOG" ]; then
  mv "$UPGRADE_LOG" "${UPGRADE_LOG}.prev" 2>/dev/null || true
fi
: > "$UPGRADE_LOG" 2>/dev/null || true

# Support both Odoo's standard env vars (HOST, USER, PASSWORD) and DB_* variants
DB_HOST=${HOST:-${DB_HOST:-postgres}}
DB_USER=${USER:-${DB_USER:-odoo}}
DB_PASSWORD=${PASSWORD:-${DB_PASSWORD:-odoo}}
DB_NAME=${DB_NAME:-tvbo}

export PGPASSWORD="$DB_PASSWORD"

# Install tvbo. The /tmp/tvbo editable mount makes the package importable once
# linked; an existing install survives container restarts and works offline, so
# prefer it. Otherwise do an editable install without build isolation (no network
# needed when the build backend is already present), then fall back to PyPI.
# Never hard-fail here (set -e): if tvbo ends up importable, that's enough.
if python3 -c "import tvbo" 2>/dev/null; then
  log "✓ tvbo already importable (editable mount)"
elif [ -d "/tmp/tvbo" ] && [ -f "/tmp/tvbo/pyproject.toml" ]; then
  log "Installing tvbo from /tmp/tvbo in editable mode..."
  if pip3 install --break-system-packages --no-build-isolation -e /tmp/tvbo > /dev/null 2>&1; then
    log "✓ tvbo installed in editable mode"
  elif python3 -c "import tvbo" 2>/dev/null; then
    log "✓ tvbo importable despite editable-install error"
  else
    log "⚠ tvbo editable install failed and tvbo is not importable"
  fi
else
  log "Installing tvbo from PyPI..."
  pip3 install --break-system-packages tvbo > /dev/null 2>&1 || log "⚠ tvbo PyPI install failed"
  log "✓ tvbo install attempted from PyPI"
fi

# Wait for PostgreSQL to be ready
log "Waiting for PostgreSQL at $DB_HOST..."
until pg_isready -h "$DB_HOST" -U "$DB_USER" -d postgres > /dev/null 2>&1; do
  sleep 2
done
log "✓ PostgreSQL is ready"

# Optional: drop and recreate database from scratch (set RESET_DB=1 in env)
if [ "${RESET_DB:-0}" = "1" ] || [ "${RESET_DB:-false}" = "true" ] || [ "${RESET_DB:-FALSE}" = "TRUE" ]; then
  log "⚠️  RESET_DB=$RESET_DB — dropping database '$DB_NAME'"
  # Terminate any existing connections to the DB
  psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true
  psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";"
  log "✓ Database '$DB_NAME' dropped — will be recreated below"
fi

# Check if database exists AND is initialized
if psql -h "$DB_HOST" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  log "Database '$DB_NAME' exists"

  # Check if database is initialized by checking for ir_module_module table
  if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='ir_module_module'" | grep -q 1; then
    log "Database is initialized"
    # Only upgrade if explicitly requested via TVBO_UPGRADE=1
    if [ "${TVBO_UPGRADE:-0}" = "1" ]; then
      reconcile_schema pre   # bridge conflicting columns before Odoo's auto sync

      log "Upgrading TVBO module..."
      upgrade_rc=0
      run_odoo_soft -d "$DB_NAME" -u tvbo --stop-after-init --without-demo=True \
        --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
        --log-level=info || upgrade_rc=$?
      if [ "$upgrade_rc" -ne 0 ]; then
        # Known stale-Many2many-_rel abort: drop the offending table and retry
        # once. Anything else is a real failure — surface it normally.
        if drop_stale_m2m_from_log "$UPGRADE_LOG"; then
          log "Retrying TVBO upgrade after dropping stale relation table(s)..."
          run_odoo -d "$DB_NAME" -u tvbo --stop-after-init --without-demo=True \
            --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
            --log-level=info
        else
          handle_odoo_failure "$upgrade_rc" \
            "-d $DB_NAME -u tvbo (no recoverable stale _rel table in log)"
        fi
      fi
      log "✓ TVBO module upgraded"

      reconcile_schema post  # re-link stashed enum text now that FK columns exist
    else
      log "Skipping upgrade (set TVBO_UPGRADE=1 to force)"
    fi
  else
    log "Database exists but is not initialized - initializing..."
    run_odoo -d "$DB_NAME" -i base,website --stop-after-init --without-demo=True \
      --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
      --log-level=warn
    log "✓ Base modules installed"

    log "Installing TVBO module..."
    run_odoo -d "$DB_NAME" -i tvbo --stop-after-init --without-demo=True \
      --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
      --log-level=info
    log "✓ TVBO module installed"
  fi
else
  log "Creating database '$DB_NAME' and installing base modules..."
  run_odoo -d "$DB_NAME" -i base,website --stop-after-init --without-demo=True \
    --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
    --log-level=warn
  log "✓ Base modules installed"

  log "Installing TVBO module..."
  run_odoo -d "$DB_NAME" -i tvbo --stop-after-init --without-demo=True \
    --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
    --log-level=info
  log "✓ TVBO module installed"
fi

# Mark website configurator as done to skip the wizard
log "Configuring website..."
if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
  -c "INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date) VALUES ('website.configurator_done', 'True', 1, NOW(), 1, NOW()) ON CONFLICT (key) DO UPDATE SET value = 'True', write_date = NOW();" > /dev/null 2>&1; then
  psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "UPDATE website SET configurator_done = true;" > /dev/null 2>&1 || true
  log "✓ Website configured"
else
  log "⚠ Could not configure website (non-critical)"
fi

log "✓ TVBO initialization complete"
log "Starting Odoo server on port 8069..."
exec odoo -d "$DB_NAME" \
  --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --db-filter="^${DB_NAME}$" \
  --log-level=${ODOO_LOG_LEVEL:-info} \
  "$@"
