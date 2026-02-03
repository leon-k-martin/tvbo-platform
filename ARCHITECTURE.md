# TVB-O Platform Architecture

## Overview

TVB-O Platform is a modular system for the Virtual Brain Ontology, consisting of separate services that communicate via APIs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TVB-O Platform                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│   │   tvbo-odoo     │      │      tvbo       │      │    tvbo-db      │    │
│   │   (Frontend)    │      │    (Compute)    │      │   (Database)    │    │
│   │                 │      │                 │      │                 │    │
│   │  • Odoo 19      │ REST │  • FastAPI      │      │  • PostgreSQL   │    │
│   │  • Web UI       │─────▶│  • Simulations  │      │  • Odoo data    │    │
│   │  • KG Browser   │ API  │  • AUTO-07p     │      │  • KG metadata  │    │
│   │  • Model viewer │      │  • Jupyter      │      │                 │    │
│   │                 │      │                 │      │                 │    │
│   └────────┬────────┘      └─────────────────┘      └────────┬────────┘    │
│            │                                                  │             │
│            └──────────────────────────────────────────────────┘             │
│                              Database connection                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Services

### 1. tvbo-odoo (Frontend)
**Image:** `git.bihealth.org:5050/tvbo/tvb-o-platform:latest`

| Aspect | Details |
|--------|---------|
| Base | Odoo 19 |
| Purpose | Web frontend, user management, knowledge graph browser |
| Python deps | `tvbo` (for model loading/display only) |
| Port | 8069 (internal), 8169 (external) |

**Responsibilities:**
- Serve web UI
- User authentication
- Knowledge graph browsing
- Model metadata display
- Delegate heavy compute to tvbo service

### 2. tvbo (Compute)
**Image:** `ghcr.io/virtual-twin/tvbo:latest`

| Aspect | Details |
|--------|---------|
| Base | Python 3.13-slim |
| Purpose | Computational backend, API, Jupyter |
| Key deps | tvbo, tvboptim, AUTO-07p, JAX |
| Ports | 8000 (API), 8888 (Jupyter) |

**Responsibilities:**
- Run simulations
- Bifurcation analysis (AUTO-07p)
- Model code generation
- Optimization workflows
- Interactive notebooks

**Modes:**
```bash
MODE=api      # FastAPI server (default)
MODE=jupyter  # Jupyter Lab
```

### 3. tvbo-db (Database)
**Image:** `postgres:15`

| Aspect | Details |
|--------|---------|
| Purpose | Persistent storage |
| Port | 5432 |
| Volume | `tvbo-db-data` |

## Communication Patterns

```
┌──────────┐     HTTP/REST      ┌──────────┐
│  Browser │ ─────────────────▶ │  Odoo    │
└──────────┘                    └────┬─────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │ tvbo API │    │ Postgres │    │  Static  │
              │ :8000    │    │ :5432    │    │  files   │
              └──────────┘    └──────────┘    └──────────┘
```

### API Endpoints (tvbo)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | GET | List all models |
| `/api/models/{name}` | GET | Get model details |
| `/api/models/{name}/report` | GET | Get markdown report |
| `/api/simulate` | POST | Run simulation |
| `/api/health` | GET | Health check |

## Local Development Setup

```yaml
# docker-compose.yml structure
services:
  odoo:
    build: Dockerfile.odoo
    ports: ["8169:8069"]
    depends_on: [postgres, tvbo]

  tvbo:
    image: ghcr.io/virtual-twin/tvbo:dev
    ports: ["8000:8000"]
    environment:
      MODE: api

  postgres:
    image: postgres:15
    volumes: [tvbo-db-data:/var/lib/postgresql/data]
```

### Commands

```bash
make up           # Start all services
make down         # Stop all services
make update-odoo  # Reload Odoo module after XML changes
make logs-odoo    # View Odoo logs
make rebuild      # Rebuild containers
```

## Production Deployment

### Option A: Docker Compose (Simple)

Same as development, with:
- External PostgreSQL (managed database)
- Reverse proxy (nginx/traefik) for HTTPS
- Volume mounts for persistent data

```
┌─────────────┐     HTTPS     ┌─────────────┐
│   Internet  │ ────────────▶ │   Traefik   │
└─────────────┘               └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │   Odoo   │    │   tvbo   │    │ Postgres │
              │  :8069   │    │  :8000   │    │ (managed)│
              └──────────┘    └──────────┘    └──────────┘
```

### Option B: Kubernetes (Scalable)

```yaml
# Namespace: tvbo
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Ingress                             │   │
│  │              (nginx-ingress / traefik)                   │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│         ┌─────────────────┴─────────────────┐                  │
│         │                                   │                  │
│         ▼                                   ▼                  │
│  ┌─────────────────┐               ┌─────────────────┐        │
│  │  Deployment:    │               │  Deployment:    │        │
│  │  tvbo-odoo      │               │  tvbo-api       │        │
│  │  replicas: 2    │               │  replicas: 2    │        │
│  └────────┬────────┘               └────────┬────────┘        │
│           │                                 │                  │
│           │         ┌───────────────────────┘                  │
│           │         │                                          │
│           ▼         ▼                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Service: postgres                     │   │
│  │              (or external managed DB)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │  PVC: odoo-data │      │  PVC: pg-data   │                  │
│  └─────────────────┘      └─────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Kubernetes Resources

```yaml
# Deployment: tvbo-odoo
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tvbo-odoo
  namespace: tvbo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tvbo-odoo
  template:
    spec:
      containers:
      - name: odoo
        image: git.bihealth.org:5050/tvbo/tvb-o-platform:latest
        ports:
        - containerPort: 8069
        env:
        - name: TVBO_API_URL
          value: "http://tvbo-api:8000"
---
# Deployment: tvbo-api
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tvbo-api
  namespace: tvbo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tvbo-api
  template:
    spec:
      containers:
      - name: tvbo
        image: ghcr.io/virtual-twin/tvbo:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODE
          value: "api"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "8Gi"
            cpu: "4"
---
# HorizontalPodAutoscaler for compute
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tvbo-api-hpa
  namespace: tvbo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tvbo-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Scaling Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| tvbo-odoo | Horizontal (stateless, behind load balancer) |
| tvbo-api | Horizontal (CPU-bound, autoscale on load) |
| postgres | Vertical (or managed DB with read replicas) |

### Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `TVBO_API_URL` | odoo | URL to tvbo API service |
| `MODE` | tvbo | `api` or `jupyter` |
| `DATABASE_URL` | odoo | PostgreSQL connection string |
| `POSTGRES_*` | postgres | DB credentials |

## Container Registries

| Service | Registry | Image |
|---------|----------|-------|
| tvbo | GitHub Container Registry | `ghcr.io/virtual-twin/tvbo` |
| tvbo-odoo | BIH GitLab Registry | `git.bihealth.org:5050/tvbo/tvb-o-platform` |

## CI/CD

### tvbo (GitHub Actions)
- Trigger: Push to `main`, `dev`, or tags
- Builds: Multi-platform (amd64 + arm64)
- Pushes to: `ghcr.io/virtual-twin/tvbo`

### tvbo-platform (GitLab CI)
- Trigger: Push to `main`, `dev`, or tags
- Builds: Multi-platform (amd64 + arm64)
- Pushes to: `git.bihealth.org:5050/tvbo/tvb-o-platform`

## Security Considerations

1. **Network isolation**: Services communicate via internal Docker/K8s network
2. **Secrets management**: Use K8s Secrets or Docker secrets for credentials
3. **HTTPS**: Terminate TLS at ingress/reverse proxy
4. **Image scanning**: Enable container scanning in CI pipelines
5. **RBAC**: Implement role-based access in Odoo for user management

## Monitoring (Future)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Prometheus  │───▶│   Grafana    │    │   Loki       │
│  (metrics)   │    │ (dashboards) │    │   (logs)     │
└──────────────┘    └──────────────┘    └──────────────┘
       ▲                                       ▲
       │                                       │
       └───────────────┬───────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
    ┌────┴────┐               ┌──────┴─────┐
    │  Odoo   │               │   tvbo     │
    └─────────┘               └────────────┘
```
