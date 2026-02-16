# TVB-O Platform Makefile
# Supports both local development (docker-compose) and production (Kubernetes)

.PHONY: help dev-up dev-down dev-restart dev-update dev-logs dev-logs-odoo dev-build dev-shell \
        up down restart update-odoo logs logs-odoo logs-api status forward forward-all

# ================================
# DEVELOPMENT MODE (Docker Compose)
# ================================
# Fast iteration: code mounted as volumes, --dev mode, no registry push/pull

dev-up:
	@echo "Starting LOCAL DEV environment..."
	@echo "Code mounted as volumes - changes are immediate!"
	docker compose up -d
	@echo ""
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "Access Odoo:  http://localhost:8070"
	@echo "Access API:   http://localhost:8001"
	@echo "Postgres:     localhost:5433"
	@echo ""
	@echo "Dev mode features:"
	@echo "  - Auto-reload on file changes"
	@echo "  - No rebuild needed for code changes"
	@echo "  - QWeb template debugging"
	@echo ""
	@echo "Useful commands:"
	@echo "  make dev-logs         - Follow all logs"
	@echo "  make dev-logs-odoo    - Follow Odoo logs"
	@echo "  make dev-update       - Update TVBO module"
	@echo "  make dev-shell        - Open Odoo shell"

dev-down:
	@echo "Stopping LOCAL DEV environment..."
	docker compose down

dev-restart:
	@echo "Restarting LOCAL DEV environment..."
	docker compose restart odoo

dev-update:
	@echo "Updating TVBO module in DEV environment..."
	docker compose exec odoo odoo -d tvbo_dev -u tvbo --stop-after-init --db_host=postgres --db_user=odoo --db_password=odoo
	@echo "Restarting Odoo..."
	@$(MAKE) dev-restart
	@echo "✓ Module updated"

dev-logs:
	docker compose logs -f

dev-logs-odoo:
	docker compose logs -f odoo

dev-build:
	@echo "Building LOCAL DEV images (tvbo-platform:dev + tvbo:dev-local)..."
	docker compose build
	@echo "✓ Images built:"
	@echo "  - tvbo-platform:dev (Odoo)"
	@echo "  - tvbo:dev-local (API from /Users/leonmartin_bih/tools/tvbo)"

dev-shell:
	@echo "Opening Odoo shell (tvbo_dev database)..."
	docker compose exec odoo odoo shell -d tvbo_dev

# ================================
# PRODUCTION MODE (Kubernetes)
# ================================
# Production deployment with registry images

# Kubernetes namespace (production uses kube-system, local can use tvbo)
K8S_NAMESPACE ?= kube-system
# Local port forwarding (avoid conflicts with other Odoo projects)
LOCAL_ODOO_PORT ?= 8070
LOCAL_API_PORT ?= 8001

help:
	@echo "TVB-O Platform - Development & Production"
	@echo ""
	@echo "=== LOCAL DEVELOPMENT (Recommended) ==="
	@echo "Fast iteration with docker-compose + volume mounts:"
	@echo ""
	@echo "  make dev-up           - Start dev environment (http://localhost:8070)"
	@echo "  make dev-down         - Stop dev environment"
	@echo "  make dev-restart      - Restart Odoo"
	@echo "  make dev-update       - Update TVBO module"
	@echo "  make dev-logs         - Follow all logs"
	@echo "  make dev-logs-odoo    - Follow Odoo logs"
	@echo "  make dev-build        - Rebuild local image"
	@echo "  make dev-shell        - Open Odoo Python shell"
	@echo ""
	@echo "=== PRODUCTION (Kubernetes) ==="
	@echo "Deploy to kube-system with registry images:"
	@echo ""
	@echo "  make up           - Deploy to Kubernetes"
	@echo "  make down         - Delete deployment"
	@echo "  make restart      - Restart Odoo (pulls fresh image)"
	@echo "  make update-odoo  - Update Odoo module"
	@echo "  make status       - Show pod status"
	@echo "  make logs         - Show logs"
	@echo "  make logs-odoo    - Follow Odoo logs"
	@echo "  make forward      - Port-forward Odoo (localhost:$(LOCAL_ODOO_PORT))"
	@echo "  make forward-all  - Port-forward Odoo + API"
	@echo ""
	@echo "Configuration:"
	@echo "  K8S_NAMESPACE     - Kubernetes namespace (default: $(K8S_NAMESPACE))"
	@echo "  LOCAL_ODOO_PORT   - Local Odoo port (default: $(LOCAL_ODOO_PORT))"
	@echo "  LOCAL_API_PORT    - Local API port (default: $(LOCAL_API_PORT))"

# Deploy to Kubernetes
up:
	@echo "Deploying TVBO Platform to Kubernetes..."
	@echo "Namespace: $(K8S_NAMESPACE)"
	kubectl apply -f k8s.yaml
	@echo ""
	@echo "Waiting for pods to be ready..."
	@kubectl wait --for=condition=ready pod -l app=tvbo-postgres -n $(K8S_NAMESPACE) --timeout=60s || true
	@kubectl wait --for=condition=ready pod -l app=tvbo-api -n $(K8S_NAMESPACE) --timeout=60s || true
	@kubectl wait --for=condition=ready pod -l app=tvbo-odoo -n $(K8S_NAMESPACE) --timeout=120s || true
	@echo ""
	@echo "✓ Deployment complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  make forward      - Access Odoo at http://localhost:$(LOCAL_ODOO_PORT)"
	@echo "  make logs-odoo    - View logs"
	@echo "  make status       - Check pod status"

# Delete deployment
down:
	@echo "Deleting TVBO Platform resources..."
	@echo "Namespace: $(K8S_NAMESPACE)"
	kubectl delete -f k8s.yaml
	@echo "✓ Resources deleted"

# Restart Odoo (pulls fresh image)
restart:
	@echo "Restarting Odoo deployment..."
	kubectl rollout restart deployment/tvbo-odoo -n $(K8S_NAMESPACE)
	@echo "Waiting for new pod..."
	@kubectl wait --for=condition=ready pod -l app=tvbo-odoo -n $(K8S_NAMESPACE) --timeout=120s
	@echo "✓ Odoo restarted"

# Update/upgrade TVBO Odoo module
update-odoo:
	@echo "Upgrading TVBO module in Kubernetes..."
	@POD=$$(kubectl get pod -n $(K8S_NAMESPACE) -l app=tvbo-odoo -o jsonpath='{.items[0].metadata.name}'); \
	echo "Pod: $$POD"; \
	kubectl exec -n $(K8S_NAMESPACE) $$POD -- odoo -d tvbo_postgres -u tvbo --stop-after-init --without-demo=True
	@echo "Restarting Odoo..."
	@$(MAKE) restart
	@echo "✓ TVBO module updated"

# Show pod status
status:
	@echo "TVBO Platform Status"
	@echo "Namespace: $(K8S_NAMESPACE)"
	@echo ""
	@kubectl get pods -n $(K8S_NAMESPACE) -l app=tvbo-odoo -o wide
	@kubectl get pods -n $(K8S_NAMESPACE) -l app=tvbo-api -o wide
	@kubectl get pods -n $(K8S_NAMESPACE) -l app=tvbo-postgres -o wide
	@echo ""
	@echo "Services:"
	@kubectl get svc -n $(K8S_NAMESPACE) -l app=tvbo-odoo
	@kubectl get svc -n $(K8S_NAMESPACE) -l app=tvbo-api

# Show all logs
logs:
	@echo "Recent logs from TVBO Platform:"
	@echo ""
	@echo "=== Postgres ==="
	@kubectl logs -n $(K8S_NAMESPACE) -l app=tvbo-postgres --tail=20 || true
	@echo ""
	@echo "=== TVBO API ==="
	@kubectl logs -n $(K8S_NAMESPACE) -l app=tvbo-api --tail=20 || true
	@echo ""
	@echo "=== Odoo ==="
	@kubectl logs -n $(K8S_NAMESPACE) -l app=tvbo-odoo --tail=20 || true

# Follow Odoo logs
logs-odoo:
	@echo "Following Odoo logs (Ctrl+C to stop)..."
	kubectl logs -n $(K8S_NAMESPACE) -l app=tvbo-odoo -f

# Follow API logs
logs-api:
	@echo "Following API logs (Ctrl+C to stop)..."
	kubectl logs -n $(K8S_NAMESPACE) -l app=tvbo-api -f

# Port-forward Odoo only (avoids conflict with other Odoo projects)
forward:
	@echo "Port-forwarding Odoo to localhost:$(LOCAL_ODOO_PORT)"
	@echo "Access at: http://localhost:$(LOCAL_ODOO_PORT)"
	@echo "Press Ctrl+C to stop"
	@echo ""
	kubectl port-forward -n $(K8S_NAMESPACE) svc/odoo $(LOCAL_ODOO_PORT):8069

# Port-forward both Odoo and API
forward-all:
	@echo "Port-forwarding TVBO Platform..."
	@echo "  Odoo: http://localhost:$(LOCAL_ODOO_PORT)"
	@echo "  API:  http://localhost:$(LOCAL_API_PORT)"
	@echo "Press Ctrl+C to stop"
	@echo ""
	kubectl port-forward -n $(K8S_NAMESPACE) svc/odoo $(LOCAL_ODOO_PORT):8069 & \
	kubectl port-forward -n $(K8S_NAMESPACE) svc/tvbo-api $(LOCAL_API_PORT):8000 & \
	wait
