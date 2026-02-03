# TVB-O Platform Makefile
# Convenience commands for development

.PHONY: help up down restart update-odoo logs logs-odoo logs-api build rebuild \
        k8s-up k8s-down k8s-restart k8s-status k8s-logs k8s-logs-odoo k8s-forward k8s-forward-all

# Default database name
DB_NAME ?= tvbo
# Kubernetes namespace
K8S_NAMESPACE ?= tvbo

help:
	@echo "TVB-O Platform Commands:"
	@echo ""
	@echo "Docker Compose (Development):"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make update-odoo  - Update/upgrade TVBO Odoo module (reloads XML templates)"
	@echo "  make logs         - Follow logs for all services"
	@echo "  make logs-odoo    - Follow Odoo logs only"
	@echo "  make logs-api     - Follow API logs only"
	@echo "  make build        - Build Docker images"
	@echo "  make rebuild      - Rebuild Docker images (no cache)"
	@echo ""
	@echo "Kubernetes (Local Testing):"
	@echo "  make k8s-up       - Deploy to local Kubernetes"
	@echo "  make k8s-down     - Delete Kubernetes deployment"
	@echo "  make k8s-restart  - Restart Odoo deployment (pull fresh image)"
	@echo "  make k8s-status   - Show pod status"
	@echo "  make k8s-logs     - Show all logs"
	@echo "  make k8s-logs-odoo - Follow Odoo logs"
	@echo "  make k8s-forward  - Port-forward Odoo (localhost:8069)"
	@echo "  make k8s-forward-all - Port-forward Odoo + API"

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

# ================================
# Kubernetes Commands
# ================================

# Deploy to local Kubernetes
k8s-up:
	@echo "Deploying to Kubernetes namespace '$(K8S_NAMESPACE)'..."
	kubectl apply -f k8s.yaml
	@echo "Waiting for pods to be ready..."
	@kubectl wait --for=condition=ready pod -l app=postgres -n $(K8S_NAMESPACE) --timeout=60s
	@kubectl wait --for=condition=ready pod -l app=tvbo-api -n $(K8S_NAMESPACE) --timeout=60s
	@kubectl wait --for=condition=ready pod -l app=odoo -n $(K8S_NAMESPACE) --timeout=120s
	@echo ""
	@echo "✓ Deployment complete!"
	@echo ""
	@echo "Access Odoo: make k8s-forward"
	@echo "View logs:   make k8s-logs-odoo"

# Delete Kubernetes deployment
k8s-down:
	@echo "Deleting Kubernetes namespace '$(K8S_NAMESPACE)'..."
	kubectl delete namespace $(K8S_NAMESPACE)
	@echo "✓ Namespace deleted"

# Restart Odoo deployment (forces image pull)
k8s-restart:
	@echo "Restarting Odoo deployment..."
	kubectl rollout restart deployment/odoo -n $(K8S_NAMESPACE)
	@echo "Waiting for new pod to be ready..."
	@kubectl wait --for=condition=ready pod -l app=odoo -n $(K8S_NAMESPACE) --timeout=120s
	@echo "✓ Odoo restarted"

# Show pod status
k8s-status:
	@echo "Pods in namespace '$(K8S_NAMESPACE)':"
	@kubectl get pods -n $(K8S_NAMESPACE) -o wide

# Show all logs
k8s-logs:
	@echo "Recent logs from all pods:"
	@echo "=== Postgres ==="
	@kubectl logs -n $(K8S_NAMESPACE) -l app=postgres --tail=20 || true
	@echo ""
	@echo "=== TVBO API ==="
	@kubectl logs -n $(K8S_NAMESPACE) -l app=tvbo-api --tail=20 || true
	@echo ""
	@echo "=== Odoo ==="
	@kubectl logs -n $(K8S_NAMESPACE) -l app=odoo --tail=20 || true

# Follow Odoo logs
k8s-logs-odoo:
	kubectl logs -n $(K8S_NAMESPACE) -l app=odoo -f

# Port-forward Odoo only
k8s-forward:
	@echo "Port-forwarding Odoo to localhost:8069"
	@echo "Access at: http://localhost:8069"
	@echo "Press Ctrl+C to stop"
	kubectl port-forward -n $(K8S_NAMESPACE) svc/odoo 8069:8069

# Port-forward both Odoo and API
k8s-forward-all:
	@echo "Port-forwarding Odoo (8069) and API (8000)"
	@echo "Odoo: http://localhost:8069"
	@echo "API:  http://localhost:8000"
	@echo "Press Ctrl+C to stop"
	@echo ""
	kubectl port-forward -n $(K8S_NAMESPACE) svc/odoo 8069:8069 & \
	kubectl port-forward -n $(K8S_NAMESPACE) svc/tvbo-api 8000:8000 & \
	wait
