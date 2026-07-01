---
title: Retrieve & store via the API
access_level: public
sequence: 20
summary: Pull models and experiments into Python (public ones openly, your own with an API key) and push your own back.
thumbnail: img/api-keys.png
---

# Retrieve & store via the API

The platform exposes a small REST API so a Python script can pull models and
experiments out of the Knowledge Graph, fetch **your own** saved and shared work,
and push new experiments back, without clicking through the UI.

- **Curated (public) models and experiments** need no account.
- **Your private and shared records** need an **API key** tied to your account.

All you need is `requests` (or any HTTP client) plus the `tvbo` package to run
what you fetch.

```bash
pip install tvbo requests
```

## Get an API key

Create one once, from [**Your Account → API keys**](../account/save-to-account.md):
name a key at [`/my/api-keys`]({{base_url}}/my/api-keys) and copy it when shown
(it is displayed only once). Pass it as a **bearer token**. Keep it out of your
code by reading it from an environment variable:

```python
import os, requests

BASE = "{{base_url}}"
HEADERS = {"Authorization": f"Bearer {os.environ['TVBO_API_KEY']}"}
```

!!! warning "Treat keys like passwords"
    An API key grants access to your account. Store it in an environment variable
    or a secrets manager, never commit it, and revoke it at `/my/api-keys` if exposed.

## List what you can access

`GET /api/tvbo/v1/experiments` returns the experiments visible to you: the public
curated ones, anything **shared** with the community, and your **own private**
records (other users' private records are never listed).

```python
r = requests.get(f"{BASE}/api/tvbo/v1/experiments", headers=HEADERS)
for exp in r.json()["data"]:
    print(exp["id"], exp["label"])
```

Models work the same way at `GET /api/tvbo/v1/models`.

## Fetch one and run it

Fetch a single experiment by id as YAML and run it, loading the string straight
into a `SimulationExperiment` with no temp file:

```python
exp_id = 123  # from the list above
yaml_text = requests.get(
    f"{BASE}/api/tvbo/v1/experiments/{exp_id}?format=yaml", headers=HEADERS
).text

from tvbo import SimulationExperiment
result = SimulationExperiment.from_string(yaml_text).run()
result.plot()
```

Add `?format=json` instead of `yaml` to get a parsed JSON body. A record private
to **another** user returns `404`: it is invisible to you, not merely forbidden.

## Store an experiment from Python

`POST /api/tvbo/v1/experiments` saves an assembled experiment to your account, so
collaborators can reproduce your run by id instead of you mailing a YAML file. Use
`?visibility=private` (default) or `?visibility=shared`:

```python
yaml_text = open("experiment.yaml").read()
r = requests.post(
    f"{BASE}/api/tvbo/v1/experiments?visibility=private",
    headers={**HEADERS, "Content-Type": "application/x-yaml"},
    data=yaml_text.encode("utf-8"),
)
print(r.json())   # {'success': True, 'id': 124, 'visibility': 'private'}
```

Pushing again with the same name **replaces** your existing record in place rather
than creating a duplicate. The saved experiment then appears under
[**My Models**]({{base_url}}/my/models) and, if shared, in the
[community gallery]({{base_url}}/tvbo/models/shared). Models push the same way at
`POST /api/tvbo/v1/models`.

## Endpoints at a glance

| Method & path | What it does | Auth |
|---|---|---|
| `GET /api/tvbo/v1/experiments` | list accessible experiments | key |
| `GET /api/tvbo/v1/experiments/<id>?format=yaml\|json` | one experiment | key |
| `POST /api/tvbo/v1/experiments?visibility=private\|shared` | save/replace an experiment | key |
| `GET /api/tvbo/v1/models` · `GET /api/tvbo/v1/models/<id>` · `POST /api/tvbo/v1/models` | same, for models (Dynamics) | key |

Curated, public models also ship with the `tvbo` package itself (see
[The `tvbo` Python package](index.md)), so you only need the API for **your own**
saved and shared work.
