# -*- coding: utf-8 -*-
"""One-flow ingestion: tvbo ground-truth YAML -> validated -> Odoo records.

Run as the module's ``post_init_hook``. There is a single path from the canonical
data to the platform database:

    tvbo/database/<category>/*.yaml
        -> tvbo.data.registry (enumerate/resolve)
        -> tvbo.utils.pydantic_loader (validate against the schema)
        -> recursive Odoo create()

Because the Odoo models are generated from the same LinkML schema (alias-aware),
the validated pydantic field names line up 1:1 with the Odoo fields — the only
remapping needed is the reserved-name inverse (id->record_id, modified->is_modified).
Enums are seeded from the generated pydantic Enum classes so the values stored in
lookup models are exactly the values the data uses.
"""
import enum as _enum
import logging

_logger = logging.getLogger(__name__)

# Reserved Odoo ORM names: schema slot -> Odoo field (matches the generator).
_RESERVED = {"id": "record_id", "modified": "is_modified"}

# Registry path fragments to skip: the neuroml/ folder is a raw NeuroML→LEMS
# import staging area (the "… as LEMS" experiments and exotic dynamics), not
# curated building blocks for the model builder.
_EXCLUDE_PATH_PARTS = ("/neuroml/",)

# (pydantic class, registry category) for the building blocks to ingest.
# Curated to avoid the Observation/Function overlap on observation_models.
# ``Study`` (bibliographic sources) is seeded from the studies/ directory; the
# files are BibTeX-style records (a Study), not SimulationStudy experiment
# containers — full bibliographic detail stays in references.bib (citekey join).
_INGEST = [
    ("Dynamics", "Dynamics"),
    ("Coupling", "Coupling"),
    ("Integrator", "Integrator"),
    ("GraphGenerator", "GraphGenerator"),
    ("BrainAtlas", "BrainAtlas"),
    ("Network", "Network"),
    ("Observation", "Observation"),
    ("Continuation", "Continuation"),
    ("Study", "Study"),
    ("SimulationExperiment", "SimulationExperiment"),
]

# Classes whose ground-truth files intentionally carry fields the schema does
# not model (Study mirrors BibTeX: journal/volume/pages/… live in references.bib
# and are dropped on ingest, keeping only the citekey-anchored KG node).
_DROP_UNKNOWN = {"Study"}


# Best-effort audit trail to a file in the data volume, because addon logging
# during post_init_hook is not reliably surfaced in the install logs.
_AUDIT_PATH = "/var/lib/odoo/tvbo_ingest.log"


def _audit(msg):
    _logger.info("tvbo ingest: %s", msg)
    try:
        with open(_AUDIT_PATH, "a") as fh:
            fh.write(str(msg) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _camel_to_snake(name):
    import re
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _to_text(value):
    if isinstance(value, (list, tuple)):
        return "\n".join(str(v) for v in value)
    return value if isinstance(value, str) else str(value)


def _resolve_one(env, comodel, value, cache):
    """Resolve a single related value to a record id."""
    if comodel not in env:
        return None
    Model = env[comodel].sudo()
    if isinstance(value, dict):
        try:
            return _create_record(env, comodel, value, cache)
        except Exception as exc:  # noqa: BLE001
            _logger.warning("tvbo ingest: nested %s create failed: %s", comodel, exc)
            return None
    if isinstance(value, (str, int, float, bool)):
        # Enum / name reference: match an existing lookup record.
        key = str(value)
        cache_key = (comodel, key)
        if cache_key in cache:
            return cache[cache_key]
        rec = Model.search(["|", ("name", "=", key), ("technical_name", "=", key)], limit=1) \
            if "technical_name" in Model._fields else Model.search([("name", "=", key)], limit=1)
        if not rec and "name" in Model._fields:
            rec = Model.create({"name": key})
        rid = rec.id if rec else None
        cache[cache_key] = rid
        return rid
    return None


def _resolve_many(env, comodel, value, cache):
    items = []
    if isinstance(value, dict):
        items = list(value.values())
    elif isinstance(value, (list, tuple)):
        items = list(value)
    ids = []
    for item in items:
        rid = _resolve_one(env, comodel, item, cache)
        if rid:
            ids.append(rid)
    return ids


def _create_record(env, model_name, data, cache):
    """Recursively create an Odoo record from a schema-shaped dict; return id."""
    if model_name not in env:
        return None
    Model = env[model_name].sudo()
    fields = Model._fields
    vals = {}
    for key, value in (data or {}).items():
        if value is None:
            continue
        fname = _RESERVED.get(key, key)
        f = fields.get(fname)
        if f is None:
            continue  # field not on this model (e.g. schema extra) -> skip
        try:
            t = f.type
            if t in ("char", "text", "html"):
                vals[fname] = _to_text(value)
            elif t == "integer":
                vals[fname] = int(value)
            elif t == "float":
                vals[fname] = float(value)
            elif t == "boolean":
                vals[fname] = bool(value)
            elif t in ("date", "datetime"):
                vals[fname] = value
            elif t == "selection":
                vals[fname] = value if isinstance(value, str) else str(value)
            elif t == "json":
                vals[fname] = value
            elif t == "many2one":
                rid = _resolve_one(env, f.comodel_name, value, cache)
                if rid:
                    vals[fname] = rid
            elif t in ("many2many", "one2many"):
                ids = _resolve_many(env, f.comodel_name, value, cache)
                if ids:
                    vals[fname] = [(6, 0, ids)]
        except Exception as exc:  # noqa: BLE001
            # Degrade gracefully: skip the problematic field, keep the record.
            _logger.warning("tvbo ingest: %s.%s skipped (%s)", model_name, fname, exc)
    return Model.create(vals).id


def _seed_enums(env, datamodel):
    """Seed each enum lookup model from its generated pydantic Enum class."""
    seeded = 0
    for attr in dir(datamodel):
        obj = getattr(datamodel, attr)
        if not (isinstance(obj, type) and issubclass(obj, _enum.Enum) and obj is not _enum.Enum):
            continue
        model_name = "tvbo." + _camel_to_snake(obj.__name__)
        if model_name not in env:
            continue
        Model = env[model_name].sudo()
        for member in obj:
            value = str(member.value)
            try:
                with env.cr.savepoint():
                    if Model.search([("name", "=", value)], limit=1):
                        continue
                    Model.create({
                        "name": value,
                        "technical_name": member.name,
                        "description": (member.__doc__ or "")[:500],
                    })
                seeded += 1
            except Exception as exc:  # noqa: BLE001
                _audit(f"enum {model_name}.{value} FAILED: {exc}")
    _logger.info("tvbo ingest: seeded %d enum values", seeded)


def seed_database(env):
    """Post-install entry point: seed enums + building blocks from ground truth."""
    try:
        from tvbo.data import registry
        from tvbo.datamodel import pydantic as datamodel
        from tvbo.utils import pydantic_loader
    except ImportError as exc:  # pragma: no cover
        _logger.error("tvbo package unavailable; skipping ingestion: %s", exc)
        return

    _seed_enums(env, datamodel)
    _audit("enums seeded")

    cache = {}
    total = 0
    for pyd_cls_name, category in _INGEST:
        model_name = "tvbo." + _camel_to_snake(pyd_cls_name)
        if model_name not in env:
            _audit(f"no Odoo model {model_name}; skipping")
            continue
        try:
            names = registry.list_entries(category)
        except Exception as exc:  # noqa: BLE001
            _audit(f"cannot list {category}: {exc}")
            continue
        ok = 0
        for name in names:
            try:
                path = str(registry.resolve(category, name))
                if any(part in path for part in _EXCLUDE_PATH_PARTS):
                    continue  # skip NeuroML import staging
                # Savepoint per record: a DB-level error rolls back just this
                # record instead of aborting the whole install transaction.
                with env.cr.savepoint():
                    obj = pydantic_loader.load(
                        path, pyd_cls_name,
                        drop_unknown=(pyd_cls_name in _DROP_UNKNOWN),
                    )
                    data = obj.model_dump(mode="python", by_alias=True, exclude_none=True)
                    _create_record(env, model_name, data, cache)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                _audit(f"{category}/{name} FAILED: {type(exc).__name__}: {exc}")
        _audit(f"{model_name} -> {ok}/{len(names)} records")
        total += ok
    _audit(f"DONE: {total} building-block records created")


def post_init_hook(env):
    """Odoo post_init_hook (env). Never fail the install: ingestion problems are
    logged to the audit file; the module still installs so the platform comes up."""
    import traceback
    _audit("=== post_init_hook start ===")
    try:
        seed_database(env)
    except Exception:  # noqa: BLE001
        _audit("post_init_hook EXCEPTION:\n" + traceback.format_exc())
        _logger.exception("tvbo ingestion failed; module still installed")
