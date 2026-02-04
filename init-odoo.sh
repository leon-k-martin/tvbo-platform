#!/bin/bash
set -euo pipefail

# Logging helper
log() {
  echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $*"
}

# Support both Odoo's standard env vars (HOST, USER, PASSWORD) and DB_* variants
DB_HOST=${HOST:-${DB_HOST:-postgres}}
DB_USER=${USER:-${DB_USER:-odoo}}
DB_PASSWORD=${PASSWORD:-${DB_PASSWORD:-odoo}}
DB_NAME=${DB_NAME:-tvbo}

export PGPASSWORD="$DB_PASSWORD"

# Only install tvbo if TVBO_REINSTALL=1 is set (for development)
# The image already has tvbo pre-installed from the Dockerfile
if [ "${TVBO_REINSTALL:-0}" = "1" ] && [ -d "/tmp/tvbo" ] && [ -f "/tmp/tvbo/pyproject.toml" ]; then
  log "Reinstalling tvbo from /tmp/tvbo (development mode)..."
  pip3 install --break-system-packages --ignore-installed typing-extensions -e /tmp/tvbo > /dev/null 2>&1
  log "✓ tvbo reinstalled"
else
  log "Using pre-installed tvbo from Docker image"
fi

# Wait for PostgreSQL to be ready
log "Waiting for PostgreSQL at $DB_HOST..."
until pg_isready -h "$DB_HOST" -U "$DB_USER" -d postgres > /dev/null 2>&1; do
  sleep 2
done
log "✓ PostgreSQL is ready"

# Check if database exists AND is initialized
if psql -h "$DB_HOST" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  log "Database '$DB_NAME' exists"

  # Check if database is initialized by checking for ir_module_module table
  if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='ir_module_module'" | grep -q 1; then
    log "Database is initialized"
    # Only upgrade if explicitly requested via TVBO_UPGRADE=1
    if [ "${TVBO_UPGRADE:-0}" = "1" ]; then
      log "Upgrading TVBO module..."
      odoo -d "$DB_NAME" -u tvbo --stop-after-init --without-demo=True \
        --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
        --log-level=warn > /dev/null 2>&1
      log "✓ TVBO module upgraded"
    else
      log "Skipping upgrade (set TVBO_UPGRADE=1 to force)"
    fi
  else
    log "Database exists but is not initialized - initializing..."
    odoo -d "$DB_NAME" -i base,website --stop-after-init --without-demo=True \
      --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
      --log-level=warn > /dev/null 2>&1
    log "✓ Base modules installed"

    log "Installing TVBO module..."
    odoo -d "$DB_NAME" -i tvbo --stop-after-init --without-demo=True \
      --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
      --log-level=warn > /dev/null 2>&1
    log "✓ TVBO module installed"
  fi
else
  log "Creating database '$DB_NAME' and installing base modules..."
  odoo -d "$DB_NAME" -i base,website --stop-after-init --without-demo=True \
    --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
    --log-level=warn > /dev/null 2>&1
  log "✓ Base modules installed"

  log "Installing TVBO module..."
  odoo -d "$DB_NAME" -i tvbo --stop-after-init --without-demo=True \
    --db_host="$DB_HOST" --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
    --log-level=warn > /dev/null 2>&1
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
  --log-level=info
