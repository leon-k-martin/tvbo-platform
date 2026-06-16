# Model builder tests

Two layers, both validating with **tvbo-native** processes only.

## 1. Python validation harness — `validate_experiment.py`

Validates an experiment YAML by importing it into tvbo:

```bash
.venv/bin/python tests/validate_experiment.py path/to/experiment.yaml          # strict Pydantic gate
.venv/bin/python tests/validate_experiment.py path/to/experiment.yaml --runtime # + advisory runtime load
cat experiment.yaml | .venv/bin/python tests/validate_experiment.py - --target Dynamics
```

Exit code 0 ⇔ valid. The strict Pydantic check (`tvbo.utils.pydantic_loader`) is the
gate; `--runtime` (`SimulationExperiment.from_string`) is advisory because it also
resolves connectivity data files.

## 2. Playwright e2e — `e2e/`

Drives the live builder at `http://localhost:8169/tvbo/configurator` and validates the
YAML it produces through the harness above.

```bash
make dev-up                     # start odoo + postgres (builder is public, no login)
cd tests/e2e
npm install && npx playwright install chromium   # first time only
npx playwright test             # run the suite
```

Env overrides: `TVBO_BASE_URL` (default `http://localhost:8169`),
`TVBO_PYTHON` (default `../../.venv/bin/python`).

Coverage: page renders; schema exposes pickable building blocks; **all seeded
experiments → valid YAML**; UI load + Download → valid; `/serialize` (keyed + list
forms); structured validation errors; from-scratch assembly; tvboptim `class_reference`
interop.

### Portal: save & share models — `specs/portal.spec.ts`

Drives the ownership/visibility flow against the live stack: a portal user saves a
model (→ `/my/models`, private by default), private models stay out of the public
list / public detail page / other users' galleries, sharing surfaces a model to
every logged-in user, and only the owner can re-private or delete it.

Extra env: `TVBO_DB` (default `tvbo_dev`), `TVBO_ADMIN_LOGIN` / `TVBO_ADMIN_PASSWORD`
(default `admin`/`admin`) — admin is used only to provision two throwaway portal
users; the records and users it creates are name-stamped per run.
