# tvbo-platform-client

Load and push your saved + shared TVBO models and SimulationExperiments from
Python, using a personal API key.

## Install

```bash
pip install ./clients/python            # from this repo
# or, if you already have the tvbo package, the same client ships as `tvbo.platform`
```

## Authenticate

Mint a key at `<platform>/my/api-keys` (shown once). Then:

```python
from tvbo_platform import TVBOPlatform          # or: from tvbo.platform import TVBOPlatform

tvbo = TVBOPlatform(base_url="https://platform.example", api_key="tvbo_…")
```

## Use

```python
# Browse
tvbo.list_models()                 # public ground-truth + shared + your own
tvbo.list_models(mine=True)        # only yours
tvbo.list_experiments()

# Load into tvbo objects (requires the `tvbo` package)
dyn = tvbo.load_model(42)          # -> Dynamics
exp = tvbo.load_experiment(123)    # -> SimulationExperiment

# …or get raw YAML / JSON, no tvbo dependency
yaml_text = tvbo.get_experiment_yaml(123)
spec = tvbo.get_model_dict(42)

# Push back (YAML string, dict, or a tvbo object)
tvbo.push_model(open("my_model.yaml").read(), visibility="private")
tvbo.push_experiment(exp, visibility="shared")
```

Pushing an element whose `name` matches one you already own updates it in place
rather than creating a duplicate.

## REST endpoints (for non-Python clients)

All require `Authorization: Bearer <key>`.

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/api/tvbo/v1/models` | list accessible models |
| GET  | `/api/tvbo/v1/models/<id>?format=yaml\|json` | one model |
| POST | `/api/tvbo/v1/models` | push a model (YAML body, or `{"yaml": …, "visibility": …}`) |
| GET  | `/api/tvbo/v1/experiments` | list accessible experiments |
| GET  | `/api/tvbo/v1/experiments/<id>?format=yaml\|json` | one experiment |
| POST | `/api/tvbo/v1/experiments` | push an experiment |
