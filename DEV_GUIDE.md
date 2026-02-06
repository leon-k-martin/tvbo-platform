# TVB-O Platform Development Guide

## Development Modes

TVB-O Platform supports two deployment modes:

1. **Local Development** (docker-compose) - Fast iteration, immediate updates
2. **Production** (Kubernetes) - Production deployment with registry images

## 🚀 Quick Start: Local Development (Recommended)

For day-to-day development with immediate code updates:

```bash
# Start dev environment
make dev-up
# Access: http://localhost:8070

# Make changes to code in odoo-addons/tvbo/...
# Changes are immediately visible! Just refresh browser (Ctrl+Shift+R)

# If you changed Python models or XML:
make dev-update

# View logs
make dev-logs-odoo

# Stop when done
make dev-down
```

### How Local Dev Works

- **Volume Mounts**: Your code at `./odoo-addons/tvbo` is mounted into the container
- **Dev Mode**: Odoo runs with `--dev=reload,qweb,werkzeug,xml` for auto-reload
- **No Registry**: Uses local `tvbo-platform:dev` image - no push/pull needed
- **Separate Ports**: 8070 (Odoo), 8001 (API), 5433 (Postgres) to avoid conflicts

### What Requires Rebuild vs Update

| Change Type | Action Needed |
|-------------|---------------|
| JavaScript files | Just refresh browser (Ctrl+Shift+R) |
| CSS files | Just refresh browser (Ctrl+Shift+R) |
| XML templates | `make dev-update` (reloads module) |
| Python models | `make dev-update` (reloads module) |
| Dockerfile changes | `make dev-build` (rebuilds image) |
| Added Python dependencies | `make dev-build` (rebuilds image) |

### Common Dev Commands

```bash
# Restart Odoo only
make dev-restart

# Open Python shell
make dev-shell

# Rebuild local image (after Dockerfile changes)
make dev-build

# View all logs
make dev-logs
```

## 🌐 Production Deployment (Kubernetes)

For production deployment to `kube-system` namespace:

```bash
# Deploy to Kubernetes
make up

# Port-forward to access locally
make forward
# Access: http://localhost:8070

# Update module (pulls fresh image from registry)
make update-odoo

# Restart (pulls fresh image)
make restart

# View status
make status

# View logs
make logs-odoo
```

### Production Requirements

- Images must be pushed to registry first:
  - `ghcr.io/leon-k-martin/tvbo-platform:main` (Odoo)
  - `leonmartin2/tvbo:dev` (API)
- Uses `imagePullPolicy: Always` to get latest
- Deployed to `kube-system` namespace by default
- Production database credentials via secret

### Configuration

Set these variables to customize:

```bash
# Change Kubernetes namespace
K8S_NAMESPACE=tvbo make up

# Change local port forwarding
LOCAL_ODOO_PORT=9090 LOCAL_API_PORT=9091 make forward-all
```

## 📁 Project Structure

```
tvbo-platform/
├── Makefile                    # All commands (dev + prod)
├── docker-compose.dev.yml      # Local dev setup
├── k8s.yaml                    # Production Kubernetes
├── Dockerfile.odoo             # Odoo image (used by both)
├── odoo-addons/tvbo/          # TVBO Odoo module (MOUNTED in dev)
│   ├── __manifest__.py
│   ├── models/
│   ├── views/
│   ├── static/src/
│   │   ├── js/                # JavaScript (auto-reload in dev)
│   │   └── css/               # CSS (auto-reload in dev)
│   └── data/
```

## 🔄 Workflow Examples

### Typical Development Session

```bash
# 1. Start environment
make dev-up

# 2. Make changes to experiment_builder.js
#    - Edit odoo-addons/tvbo/static/src/js/experiment_builder.js
#    - Save file
#    - Refresh browser (Ctrl+Shift+R)
#    - Changes visible immediately!

# 3. Make changes to XML template
#    - Edit odoo-addons/tvbo/views/configurator_templates.xml
#    - Save file
#    - Run: make dev-update
#    - Refresh browser

# 4. View logs if needed
make dev-logs-odoo

# 5. Stop when done
make dev-down
```

### Pushing to Production

```bash
# 1. Test locally first
make dev-up
# ... test changes ...
make dev-down

# 2. Push to GitHub
git add .
git commit -m "Your changes"
git push origin main  # CI/CD auto-builds and pushes to ghcr.io

# 3. Wait for CI/CD to complete (check Actions tab on GitHub)

# 4. Deploy/update production
make restart  # Pulls fresh image from registry
# or
make update-odoo  # Also upgrades module
```

**Note:** CI/CD automatically builds and pushes images on push to `main` or `dev` branches. No manual docker build needed!

## 🐛 Troubleshooting

### Dev Mode: Changes not visible

1. For JS/CSS: Hard refresh browser (Ctrl+Shift+R)
2. For XML/Python: Run `make dev-update`
3. Check logs: `make dev-logs-odoo`

### Dev Mode: Port already in use

Change ports in docker-compose.dev.yml:
```yaml
ports:
  - "8071:8069"  # Changed from 8070
```

### Production: Pod not starting

```bash
# Check pod status
make status

# View logs
make logs-odoo

# Common issues:
# - Image pull errors: Check registry credentials
# - Database connection: Check postgres pod health
# - Module errors: Check Odoo logs for Python tracebacks
```

### Production: Can't access Odoo

```bash
# Check if service exists
kubectl get svc -n kube-system -l app=tvbo-odoo

# Port-forward manually
kubectl port-forward -n kube-system svc/odoo 8070:8069
```

## 🎯 Best Practices

1. **Always use dev mode for development** - Faster iteration, no registry needed
2. **Test in dev before production** - Catch issues early
3. **Use hard refresh (Ctrl+Shift+R)** - Browser caching can hide JS/CSS changes
4. **Check logs when stuck** - `make dev-logs-odoo` shows Python errors
5. **Clean up volumes** - If database gets corrupted: `docker compose -f docker-compose.dev.yml down -v`

## 🆘 Getting Help

```bash
# See all available commands
make help

# Check environment status
make dev-up && make status  # Dev
make status                  # Production
```
