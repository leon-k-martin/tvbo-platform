# TVB-O Platform

## Overview

TVB-O Platform consists of three Docker services communicating via APIs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TVB-O Platform                                 │
│                                                                             │
│   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐     │
│   │   tvbo-odoo     │ REST │      tvbo       │      │    tvbo-db      │     │
│   │   (Frontend)    │─────▶│    (Compute)    │      │   (Database)    │     │
│   │                 │ API  │                 │      │                 │     │
│   │  Odoo 19        │      │  FastAPI        │      │  PostgreSQL 17  │     │
│   │  :8169          │      │  :8000          │      │  :5432          │     │
│   └────────┬────────┘      └─────────────────┘      └────────┬────────┘     │
│            └──────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| tvbo-odoo | [`ghcr.io/leon-k-martin/tvbo-platform`](https://github.com/leon-k-martin/tvbo-platform/pkgs/container/tvbo-platform) | 8169 | Web UI, KG Browser |
| tvbo | [`ghcr.io/virtual-twin/tvbo`](https://github.com/virtual-twin/tvbo/pkgs/container/tvbo) | 8000 | API, Simulations, Jupyter |
| tvbo-db | `postgres:17` | 5432 | Database |

## Development Commands

```bash
make up           # Start all services
make down         # Stop all services
make update-odoo  # Reload Odoo module after XML changes
make logs-odoo    # View Odoo logs
make rebuild      # Rebuild containers
```

## CI/CD

Both repos use GitHub Actions to build multi-platform images (amd64 + arm64).

| Repo | Workflow | Pushes to |
|------|----------|-----------|
| [virtual-twin/tvbo](https://github.com/virtual-twin/tvbo) | [docker.yml](https://github.com/virtual-twin/tvbo/actions/workflows/docker.yml) | `ghcr.io/virtual-twin/tvbo` |
| [leon-k-martin/tvbo-platform](https://github.com/leon-k-martin/tvbo-platform) | [docker.yml](https://github.com/leon-k-martin/tvbo-platform/actions/workflows/docker.yml) | `ghcr.io/leon-k-martin/tvbo-platform` |

## API Endpoints (tvbo)

| Endpoint | Description |
|----------|-------------|
| `GET /api/models` | List all models |
| `GET /api/models/{name}` | Get model details |
| `GET /api/models/{name}/report` | Get markdown report |
| `POST /api/simulate` | Run simulation |
| `GET /api/health` | Health check |

