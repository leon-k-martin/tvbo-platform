#!/usr/bin/env python3
"""Report what ``drop_unknown=True`` silently discards on KG ingest.

The ingest loads ground-truth YAML with ``drop_unknown=True`` so a single field
the generated schema does not model (schema drift) does not lose the whole record
(GraphGenerator was 0/9 without it). The cost is silence: dropped fields vanish
with no signal. This makes the drift visible — load every ingested file with
``drop_unknown=False`` and report the extra/unknown fields per file, so the
LinkML schema can be brought back in sync deliberately instead of accumulating
invisible loss.

Run where tvbo is importable (e.g. inside the odoo/api container):
    python3 scripts/schema_drift.py
Exit 0 always (diagnostic).
"""
import collections
import re
import sys

# (pydantic class, registry category) — mirrors models/ingest.py::_INGEST.
_INGEST = [
    ("Dynamics", "Dynamics"), ("Coupling", "Coupling"), ("Integrator", "Integrator"),
    ("GraphGenerator", "GraphGenerator"), ("BrainAtlas", "BrainAtlas"), ("Network", "Network"),
    ("Observation", "Observation"), ("Continuation", "Continuation"), ("Study", "Study"),
    ("SimulationExperiment", "SimulationExperiment"), ("SimulationTool", "SimulationTool"),
]

_EXTRA_RE = re.compile(r"\n\s*([A-Za-z0-9_.\[\]]+)\s*\n\s*Extra inputs are not permitted")


def _extra_fields(exc):
    """Dotted field paths flagged 'extra_forbidden' in a pydantic error (only)."""
    errs = getattr(exc, "errors", None)
    if callable(errs):
        try:
            paths = [".".join(str(p) for p in e.get("loc", ()))
                     for e in exc.errors() if e.get("type") == "extra_forbidden"]
            if paths:
                return paths
        except Exception:  # noqa: BLE001
            pass
    return _EXTRA_RE.findall(str(exc))


def main():
    try:
        from tvbo.data import registry
        from tvbo.utils import pydantic_loader
    except ImportError as exc:  # pragma: no cover
        print("tvbo not importable:", exc)
        return 0

    field_tally = collections.Counter()
    per_category = {}
    files_with_drift = total = 0

    for cls, cat in _INGEST:
        try:
            names = registry.list_entries(cat)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{cat}] list failed: {exc}")
            continue
        cat_drift = 0
        for name in names:
            total += 1
            try:
                pydantic_loader.load(str(registry.resolve(cat, name)), cls, drop_unknown=False)
            except Exception as exc:  # noqa: BLE001
                extras = _extra_fields(exc)
                if extras:
                    files_with_drift += 1
                    cat_drift += 1
                    for p in extras:
                        field_tally[f"{cls}.{p}"] += 1
                    print(f"  DRIFT {cat}/{name}: {', '.join(sorted(set(extras)))}")
        per_category[cat] = (cat_drift, len(names))

    print("\n==== schema-drift summary ====")
    for cat, (d, n) in per_category.items():
        print(f"  {cat}: {d}/{n} files drop fields" + ("  <-- drift" if d else ""))
    print(f"\n  total: {files_with_drift}/{total} ingested files drop >=1 field under the current schema")
    if field_tally:
        print("  most-dropped fields (these are absent in the KG/DB):")
        for fld, c in field_tally.most_common(25):
            print(f"    {c:4d}  {fld}")
    print("\n  drop_unknown keeps these records; the listed fields are silently discarded.")
    print("  Bring the LinkML schema in sync to stop dropping them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
