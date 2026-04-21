#!/bin/bash
set -euo pipefail

# Ensure Python exceptions are visible (no output buffering)
export PYTHONUNBUFFERED=1

# Logging helper
log() {
  echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $*"
}

# Run odoo command with error capture (set -e would hide the traceback)
# Mirror output to /var/lib/odoo/upgrade.log so it survives container restart.
UPGRADE_LOG=/var/lib/odoo/upgrade.log
run_odoo() {
  set +e
  odoo "$@" --log-level=${ODOO_LOG_LEVEL:-debug} 2>&1 | tee -a "$UPGRADE_LOG"
  local rc=${PIPESTATUS[0]}
  set -e
  if [ $rc -ne 0 ]; then
    log "ERROR: odoo command failed with exit code $rc" | tee -a "$UPGRADE_LOG"
    log "Command was: odoo $*" | tee -a "$UPGRADE_LOG"
    log "Last 50 lines of upgrade log:" | tee -a "$UPGRADE_LOG"
    tail -50 "$UPGRADE_LOG" || true
    if [ $rc -eq 137 ] || [ $rc -eq 255 ]; then
      log "Checking dmesg for OOM..."
      dmesg 2>/dev/null | tail -20 || true
    fi
    if [ "${TVBO_KEEP_ALIVE_ON_FAIL:-0}" = "1" ]; then
      log "TVBO_KEEP_ALIVE_ON_FAIL=1 set; sleeping forever for kubectl exec debugging"
      sleep infinity
    fi
    exit $rc
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

# Install tvbo: prefer mounted source (dev), fall back to pip, then pre-installed (production)
if [ -d "/tmp/tvbo" ] && [ -f "/tmp/tvbo/pyproject.toml" ]; then
  log "Installing tvbo from /tmp/tvbo in editable mode..."
  pip3 install --break-system-packages -e /tmp/tvbo > /dev/null 2>&1
  log "✓ tvbo installed in editable mode"
elif python3 -c "import tvbo" 2>/dev/null; then
  log "✓ tvbo already installed"
else
  log "Installing tvbo from PyPI..."
  pip3 install --break-system-packages tvbo > /dev/null 2>&1
  log "✓ tvbo installed from PyPI"
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
      log "Upgrading TVBO module..."
      run_odoo -d "$DB_NAME" -u tvbo --stop-after-init --without-demo=True \
        --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
        --log-level=info
      log "✓ TVBO module upgraded"
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
  --log-level=info \
  "$@"
