# -*- coding: utf-8 -*-
"""One-flow ingestion: tvbo ground-truth YAML -> validated -> Odoo records.

Run as the module's ``post_init_hook``. There is a single path from the canonical
data to the platform database:

    tvbo/database/<category>/*.yaml
        -> tvbo.data.registry (enumerate/resolve)
        -> tvbo.utils.pydantic_loader (validate against the schema)
        -> recursive Odoo create()

Because the Odoo models are generated from the same LinkML schema (alias-aware), the validated pydantic field names line up 1:1 with the Odoo fields — the only remapping needed is the generator's ``RENAMED_SLOTS`` for slots named after Odoo's record API (e.g. id->record_id, env->record_env). Enums are seeded from the generated pydantic Enum classes so the values stored in lookup models are exactly the values the data uses.
"""
import enum as _enum
import logging
import math
import re

from . import bibliography
from .schema_models import RENAMED_SLOTS

_logger = logging.getLogger(__name__)

# Synthetic module namespace for the external IDs that make ingestion idempotent.
# Each ingested ground-truth record gets an ir.model.data row keyed by its
# (category, registry-name) here, so a re-run skips what already exists — the
# robust, field-agnostic equivalent of Odoo's own data-file idempotency. It is
# NOT a real addon, so it never enters the module graph and `-u tvbo`'s orphan
# cleanup never prunes these rows (unlike the legacy XML data that started this).
_INGEST_MODULE = "__tvbo_ingest__"


def _xmlid(category, name):
    """Deterministic, collision-free external-id name for a (category, entry)."""
    return re.sub(r"[^a-z0-9_]+", "_", f"{category}_{name}".lower()).strip("_")

# Registry path fragments to skip. Empty: the neuroml/ folder (raw NeuroML→LEMS
# import staging — the "… as LEMS" experiments and exotic dynamics) is now
# ingested too, so the KG matches the full tvbo-api ground truth. Re-add
# "/neuroml/" here to curate it back out.
_EXCLUDE_PATH_PARTS = ()

# (pydantic class, registry category) for the building blocks to ingest.
# Curated to avoid the Observation/Function overlap on observation_models.
# ``Study`` (bibliographic sources) is seeded from the studies/ directory; the
# files are BibTeX-style records (a Study), not SimulationStudy experiment
# containers — full bibliographic detail stays in references.bib (citekey join).
# ``SimulationTool`` is the software/ directory (neurolib, Brian2, Arbor, …) ->
# tvbo.simulation_tool; requires the "SimulationTool": "software" registry entry.
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
    ("SimulationTool", "SimulationTool"),
]

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


def _json_safe(value):
    """Make a value safe for a Postgres json/jsonb column.

    Non-finite floats (inf/-inf/nan) are valid Python-JSON but Postgres rejects
    them ('invalid input syntax for type json — Token "Infinity" is invalid'),
    which aborts the INSERT. Because the per-field handler keeps issuing SQL on
    the now-aborted cursor, the failure cascades (InFailedSqlTransaction) across
    the rest of the record and the WHOLE record is lost (e.g. dynamics with an
    unbounded range hi=inf: KIonEx, CoombesByrne, …). Represent the non-finite
    values as string tokens so the record still ingests and the bound round-trips
    (YAML .inf <-> "Infinity")."""
    if isinstance(value, float):
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if math.isnan(value):
            return "NaN"
        return value
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


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


def _items(value):
    """The members of a schema collection, which the data gives either as a list or as a dict keyed by each member's identifier."""
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _resolve_many(env, comodel, value, cache):
    ids = []
    for item in _items(value):
        rid = _resolve_one(env, comodel, item, cache)
        if rid:
            ids.append(rid)
    return ids


def _natural_key(Model, data):
    """Return ``(odoo_field, value)`` identifying this record for idempotency, or ``(None, None)``. Prefers the schema id (stored under its ``RENAMED_SLOTS`` field), then name, then label — whichever the model actually has and the data provides. Lets the seed run on every deploy as a gap-filling migration (skip what already exists) instead of a one-shot that needs an empty DB / RESET_DB."""
    for schema_key in ("id", "name", "label"):
        odoo_field = RENAMED_SLOTS.get(schema_key, schema_key)
        if odoo_field in Model._fields and data.get(schema_key) not in (None, ""):
            return odoo_field, data[schema_key]
    return None, None


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
        fname = RENAMED_SLOTS.get(key, key)
        f = fields.get(fname)
        if f is None:
            continue  # field not on this model (e.g. schema extra) -> skip
        try:
            # Per-field savepoint: a field whose value triggers a DB error (a bad
            # nested create, a non-castable value) must NOT abort the surrounding
            # transaction and cascade InFailedSqlTransaction onto every following
            # field/record. The savepoint rolls that one field back to a clean
            # cursor; we skip it and keep the rest of the record.
            with env.cr.savepoint():
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
                    vals[fname] = _json_safe(value)
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
            vals.pop(fname, None)
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


def _ground_truth(pydantic_loader, path, pyd_cls_name):
    """The ground-truth file at *path* as a plain dict. Fields the generated schema does not model yet (schema drift, reported by ``scripts/schema_drift.py``) are dropped, because one unknown field would otherwise fail validation and lose the whole record."""
    return pydantic_loader.load(path, pyd_cls_name, drop_unknown=True).model_dump(mode="python", by_alias=True, exclude_none=True)


def _refill_axis_parameters(env, registry, pydantic_loader):
    """Refill the empty ``parameter`` of exploration axes on ingested experiments from ground truth, matching each exploration by name and its axes by order; an exploration whose axis count no longer matches is logged and left alone. The seed skips experiments it already has, so this is what repairs an ingested axis whose value was lost."""
    refilled = 0
    for name in registry.list_entries("SimulationExperiment"):
        experiment = env.ref(f"{_INGEST_MODULE}.{_xmlid('SimulationExperiment', name)}", raise_if_not_found=False) or env["tvbo.simulation_experiment"]
        broken = experiment.sudo().explorations.filtered(lambda exploration: not all(exploration.space.mapped("parameter")))
        if not broken:
            continue
        try:
            data = _ground_truth(pydantic_loader, str(registry.resolve("SimulationExperiment", name)), "SimulationExperiment")
        except Exception as exc:  # noqa: BLE001
            _audit(f"SimulationExperiment/{name}: axis refill FAILED: {type(exc).__name__}: {exc}")
            continue
        truth = {exploration.get("name"): _items(exploration.get("space")) for exploration in _items(data.get("explorations"))}
        for exploration in broken:
            axes = exploration.space.sorted("id")
            items = truth.get(exploration.name, [])
            if len(items) != len(axes):
                _audit(f"SimulationExperiment/{name}: exploration {exploration.name} has {len(axes)} axes, ground truth {len(items)}; left as is")
                continue
            for axis, item in zip(axes, items):
                if not axis.parameter and item.get("parameter"):
                    axis.parameter = item["parameter"]
                    refilled += 1
    _audit(f"exploration axes: {refilled} empty parameter(s) refilled from ground truth")


def _refill_study_details(env):
    """Write each study's schema fields (title, authors, year, doi, type) from references.bib by its citekey, which is all a study's file holds: a curated study takes every value the bib gives, so a corrected bib reaches it, while a study someone saved keeps its own values and only fills the empty ones."""
    saved, updated = env["tvbo.model_share"].saved_ids("tvbo.study"), 0
    for study in env["tvbo.study"].sudo().search([("citekey", "!=", False)]):
        vals = {name: value for name, value in bibliography.study(study.citekey).items() if name in study._fields and study[name] != value and (study.id not in saved or not study[name])}
        if vals:
            study.write(vals)
            updated += 1
    _audit(f"studies: {updated} updated from references.bib")


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
        IMD = env["ir.model.data"].sudo()
        Model = env[model_name].sudo()
        ok = 0
        skipped = 0
        for name in names:
            try:
                path = str(registry.resolve(category, name))
                if any(part in path for part in _EXCLUDE_PATH_PARTS):
                    continue  # skip NeuroML import staging
                xmlid = _xmlid(category, name)
                # Savepoint per record: a DB-level error rolls back just this
                # record instead of aborting the whole install transaction.
                with env.cr.savepoint():
                    # Idempotent via an external id: if this (category, name) was
                    # already ingested AND its row still exists, skip it. Lets the
                    # seed run on every deploy as a gap-filling migration — no
                    # duplicates, no RESET_DB — and works for models with no natural
                    # key field (integrator, study). A marker whose row was deleted
                    # out from under it (e.g. an FK cascade bypassing the ORM, which
                    # would skip Odoo's own ir.model.data cleanup) is stale: drop it
                    # and re-create, so a dangling marker can never become a
                    # permanent gap in the KG.
                    marker = IMD.search([("module", "=", _INGEST_MODULE),
                                         ("name", "=", xmlid)], limit=1)
                    if marker:
                        if Model.browse(marker.res_id).exists():
                            skipped += 1
                            continue
                        marker.unlink()
                    data = _ground_truth(pydantic_loader, path, pyd_cls_name)
                    # Back-compat: a record from a pre-external-id ingest may already
                    # exist; adopt it (attach the external id) instead of duplicating.
                    # But NEVER adopt a row another ingest marker already owns: the
                    # natural key is not guaranteed unique (e.g. two distinct
                    # experiments both declare id=1, and record_id has no unique
                    # constraint), and collapsing them would drop one from the KG.
                    kf, kv = _natural_key(Model, data)
                    prior = Model.search([(kf, "=", kv)], limit=1) if kf else None
                    if prior and IMD.search([("module", "=", _INGEST_MODULE),
                                             ("model", "=", model_name),
                                             ("res_id", "=", prior.id)], limit=1):
                        prior = None
                    if prior:
                        rec_id = prior.id
                        skipped += 1
                    else:
                        rec_id = _create_record(env, model_name, data, cache)
                        if rec_id:
                            ok += 1
                    if rec_id:
                        IMD.create({
                            "module": _INGEST_MODULE, "name": xmlid,
                            "model": model_name, "res_id": rec_id, "noupdate": True,
                        })
            except Exception as exc:  # noqa: BLE001
                _audit(f"{category}/{name} FAILED: {type(exc).__name__}: {exc}")
        _audit(f"{model_name} -> {ok} created, {skipped} already present / {len(names)} total")
        total += ok
    _refill_axis_parameters(env, registry, pydantic_loader)
    _refill_study_details(env)
    _audit(f"DONE: {total} building-block records created this run")
    comp = kg_completeness(env)
    _audit("KG_COMPLETENESS: %s%s" % (
        comp["verdict"],
        (" | short: " + ", ".join(comp["shortfalls"])) if comp["shortfalls"] else "",
    ))


def kg_completeness(env):
    """Per-category ground-truth coverage of the KG database side — the single
    source of truth for /kg/health, the deploy banner (emit_kg_summary), and CI.

    expected = ground-truth entries the registry enumerates for the category
    (minus path exclusions); actual = number of ``__tvbo_ingest__`` external ids
    for that model, i.e. top-level ingested records, so nested-created rows never
    inflate it. Verdict: KG_EMPTY if Dynamics is empty (public KG would show only
    the ontology), KG_DEGRADED if any category is below its ground-truth count,
    else KG_OK. Never raises: returns KG_UNKNOWN if the ground truth is missing."""
    try:
        from tvbo.data import registry
    except ImportError as exc:  # pragma: no cover
        return {"verdict": "KG_UNKNOWN", "categories": {}, "shortfalls": ["tvbo unavailable: %s" % exc]}
    IMD = env["ir.model.data"].sudo()
    cats, shortfalls = {}, []
    for pyd_cls_name, category in _INGEST:
        model_name = "tvbo." + _camel_to_snake(pyd_cls_name)
        try:
            names = registry.list_entries(category)
            if _EXCLUDE_PATH_PARTS:
                names = [n for n in names if not any(
                    p in str(registry.resolve(category, n)) for p in _EXCLUDE_PATH_PARTS)]
            expected = len(names)
        except Exception:  # noqa: BLE001
            expected = None
        actual = (IMD.search_count([("module", "=", _INGEST_MODULE), ("model", "=", model_name)])
                  if model_name in env else 0)
        ok = expected is not None and actual >= expected
        cats[category] = {"model": model_name, "expected": expected, "actual": actual, "ok": ok}
        if expected and actual < expected:
            shortfalls.append("%s %d/%d" % (category, actual, expected))
    if not cats.get("Dynamics", {}).get("actual"):
        verdict = "KG_EMPTY"
    elif shortfalls:
        verdict = "KG_DEGRADED"
    else:
        verdict = "KG_OK"
    return {"verdict": verdict, "categories": cats, "shortfalls": shortfalls}


def registry_coverage():
    """Registry categories whose data directory NO ``_INGEST`` entry covers.

    The software outage's second act was a category present in the ground-truth
    registry (``software/``) that ``_INGEST`` simply forgot to list, so 64 records
    never reached the KG. This catches that class of bug as a pure config check
    (no DB needed): every directory the registry exposes for enumeration must be
    ingested by some ``_INGEST`` entry. Alias categories that resolve to an
    already-ingested dir (``SimulationStudy``->studies, ``Function``->
    observation_models) count as covered. Returns ``[]`` when fully covered."""
    try:
        from tvbo.data import registry
        cats = dict(registry._CATEGORIES)
    except Exception:  # noqa: BLE001
        return []
    ingested_dirs = {cats[c] for _, c in _INGEST if c in cats}
    return [{"category": cat, "dir": d}
            for cat, d in sorted(cats.items()) if d not in ingested_dirs]


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
