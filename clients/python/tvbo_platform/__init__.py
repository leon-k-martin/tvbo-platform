"""Python client for the TVBO platform REST API.

Load and push your saved + shared models and SimulationExperiments using a
personal API key (mint one at ``<platform>/my/api-keys``).

    from tvbo_platform import TVBOPlatform

    tvbo = TVBOPlatform(base_url="https://platform.example", api_key="tvbo_…")
    for m in tvbo.list_models(mine=True):
        print(m["id"], m["name"], m["visibility"])

    exp = tvbo.load_experiment(123)        # -> tvbo SimulationExperiment (if tvbo installed)
    yaml_text = tvbo.get_experiment_yaml(123)

    tvbo.push_experiment(exp, visibility="shared")
    tvbo.push_model(open("my_model.yaml").read())

The ``load_*`` helpers parse into tvbo objects and therefore require the ``tvbo``
package; the ``get_*_yaml`` helpers return raw YAML and have no such dependency.
"""
from __future__ import annotations

__all__ = ["TVBOPlatform", "TVBOPlatformError"]

import requests


class TVBOPlatformError(RuntimeError):
    """Raised when the platform returns an error response."""


class TVBOPlatform:
    def __init__(self, base_url: str, api_key: str, timeout: int = 60):
        if not base_url or not api_key:
            raise ValueError("base_url and api_key are required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {api_key}"

    # -- HTTP -----------------------------------------------------------
    def _get(self, path: str, **params):
        resp = self._session.get(self.base_url + path, params=params, timeout=self.timeout)
        return self._checked(resp)

    def _post(self, path: str, payload: dict):
        resp = self._session.post(self.base_url + path, json=payload, timeout=self.timeout)
        return self._checked(resp)

    @staticmethod
    def _checked(resp):
        if resp.status_code == 401:
            raise TVBOPlatformError("Unauthorized — check your API key.")
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json()
            except ValueError:
                pass
            raise TVBOPlatformError(f"HTTP {resp.status_code}: {detail}")
        return resp

    # -- models ---------------------------------------------------------
    def list_models(self, mine: bool = False) -> list:
        data = self._get("/api/tvbo/v1/models").json()["data"]
        return [m for m in data if m.get("mine")] if mine else data

    def get_model_yaml(self, model_id: int) -> str:
        return self._get(f"/api/tvbo/v1/models/{model_id}", format="yaml").text

    def get_model_dict(self, model_id: int) -> dict:
        return self._get(f"/api/tvbo/v1/models/{model_id}", format="json").json()["data"]

    def load_model(self, model_id: int):
        """Parse the model into a tvbo ``Dynamics`` object (needs tvbo installed)."""
        from tvbo.utils import pydantic_loader

        return pydantic_loader.loads(self.get_model_yaml(model_id), "Dynamics")

    def push_model(self, spec, visibility: str = "private") -> dict:
        """Save a model. ``spec`` may be YAML text, a dict, or a tvbo object."""
        return self._post(
            "/api/tvbo/v1/models",
            {"yaml": _to_yaml(spec), "visibility": visibility},
        ).json()

    # -- experiments ----------------------------------------------------
    def list_experiments(self) -> list:
        return self._get("/api/tvbo/v1/experiments").json()["data"]

    def get_experiment_yaml(self, experiment_id: int) -> str:
        return self._get(f"/api/tvbo/v1/experiments/{experiment_id}", format="yaml").text

    def get_experiment_dict(self, experiment_id: int) -> dict:
        return self._get(
            f"/api/tvbo/v1/experiments/{experiment_id}", format="json"
        ).json()["data"]

    def load_experiment(self, experiment_id: int):
        """Parse into a tvbo ``SimulationExperiment`` (needs tvbo installed)."""
        from tvbo.classes.experiment import SimulationExperiment

        return SimulationExperiment.from_string(self.get_experiment_yaml(experiment_id))

    def push_experiment(self, spec, visibility: str = "private") -> dict:
        """Save an experiment. ``spec`` may be YAML text, a dict, or a tvbo object."""
        return self._post(
            "/api/tvbo/v1/experiments",
            {"yaml": _to_yaml(spec), "visibility": visibility},
        ).json()


def _to_yaml(spec) -> str:
    """Coerce a YAML string / dict / tvbo object into schema YAML text."""
    if isinstance(spec, str):
        return spec
    if isinstance(spec, dict):
        import yaml

        return yaml.safe_dump(spec, sort_keys=False)
    # tvbo pydantic objects serialize through the loader's dumper.
    try:
        from tvbo.utils import pydantic_loader

        if hasattr(spec, "model_dump"):
            return pydantic_loader.dump(spec)
    except Exception:  # pragma: no cover - tvbo optional
        pass
    for attr in ("to_string", "to_yaml"):
        if hasattr(spec, attr):
            return getattr(spec, attr)()
    raise TypeError(
        "Unsupported spec type for push; pass YAML text, a dict, or a tvbo object."
    )
