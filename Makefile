# TVB-O Platform Makefile
# Convenience commands for development

.PHONY: help up down restart update-odoo logs logs-odoo logs-api build rebuild

# Default database name
DB_NAME ?= tvbo

help:
	@echo "TVB-O Platform Commands:"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make update-odoo  - Update/upgrade TVBO Odoo module (reloads XML templates)"
	@echo "  make logs         - Follow logs for all services"
	@echo "  make logs-odoo    - Follow Odoo logs only"
	@echo "  make logs-api     - Follow API logs only"
	@echo "  make build        - Build Docker images"
	@echo "  make rebuild      - Rebuild Docker images (no cache)"

# Start services
up:
	docker compose up -d

# Stop services
down:
	docker compose down

# Restart services
restart:
	docker compose restart

# Update/upgrade TVBO Odoo module - reloads XML templates from disk
update-odoo:
	@echo "Upgrading TVBO module..."
	docker compose exec odoo odoo -d $(DB_NAME) -u tvbo --stop-after-init --without-demo=True \
		--db_host=postgres --db_user=odoo --db_password=odoo
	@echo "Restarting Odoo container..."
	docker compose restart odoo
	@echo "Done! TVBO module updated."

# View logs
logs:
	docker compose logs -f

logs-odoo:
	docker compose logs -f odoo

logs-api:
	docker compose logs -f tvbo-api

# Build images
build:
	docker compose build

rebuild:
	docker compose build --no-cache
