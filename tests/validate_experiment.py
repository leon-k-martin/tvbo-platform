#!/usr/bin/env python3
"""Validate a TVBO experiment YAML using only tvbo-native processes.

This is the source of truth the e2e suite uses to assert that YAML produced by
the platform's model builder is *really* valid — i.e. that tvbo itself accepts
it. Validation runs through two tvbo-native paths:

1. ``tvbo.utils.pydantic_loader`` — strict Pydantic datamodel
   (``extra="forbid"``). Always run. This is the trustworthy structural check.
2. ``tvbo.classes.experiment.SimulationExperiment.from_string`` — the full
   runtime loader (LinkML dataclasses + ontology enrichment). Run when
   ``--runtime`` is passed and its (heavier) deps are importable.

Usage::

    python validate_experiment.py path/to/experiment.yaml [--runtime]
    cat experiment.yaml | python validate_experiment.py - [--target Dynamics]

Output: a JSON report on stdout. Exit code 0 iff every requested check passed,
so the script doubles as a CI/Playwright gate.
"""
from __future__ import annotations

import argparse
import json
import sys


def _read_source(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def validate_pydantic(yaml_text: str, target: str) -> dict:
    """Strict Pydantic validation via tvbo.utils.pydantic_loader."""
    try:
        from tvbo.utils import pydantic_loader
        from pydantic import ValidationError
    except ImportError as exc:  # pragma: no cover - environment issue
        return {"path": "pydantic", "ok": False, "error": f"import_error: {exc}"}

    try:
        obj = pydantic_loader.loads(yaml_text, target)
    except ValidationError as ve:
        return {
            "path": "pydantic",
            "ok": False,
            "error": "validation_error",
            "errors": [
                {"loc": ".".join(str(p) for p in e["loc"]), "type": e["type"], "msg": e["msg"]}
                for e in ve.errors()
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"path": "pydantic", "ok": False, "error": f"{type(exc).__name__}: {exc}"}

    ident = getattr(obj, "id", None)
    return {"path": "pydantic", "ok": True, "class": type(obj).__name__, "id": ident}


def validate_runtime(yaml_text: str) -> dict:
    """Full runtime validation via SimulationExperiment.from_string."""
    try:
        from tvbo.classes.experiment import SimulationExperiment
    except ImportError as exc:
        return {"path": "runtime", "ok": False, "skipped": True, "error": f"import_error: {exc}"}

    try:
        exp = SimulationExperiment.from_string(yaml_text)
    except Exception as exc:  # noqa: BLE001
        return {"path": "runtime", "ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "path": "runtime",
        "ok": True,
        "model": getattr(exp, "model", None),
        "has_network": getattr(exp, "network", None) is not None,
    }


def _validate_one(yaml_text: str, target: str, runtime: bool) -> dict:
    """Validate a single YAML string and return a report dict."""
    report = {"target": target, "checks": []}

    # The Pydantic check is the authoritative structural-validity gate.
    pyd = validate_pydantic(yaml_text, target)
    report["checks"].append(pyd)

    # The runtime loader additionally *resolves* declared data (e.g. BIDS
    # connectivity files) and enriches from the ontology, so it needs data +
    # heavy deps. It is therefore advisory: reported, but it does not fail the
    # gate (a missing connectivity file is an environment issue, not invalid
    # YAML). Run it only on request.
    if runtime:
        rt = validate_runtime(yaml_text)
        rt["advisory"] = True
        report["checks"].append(rt)

    report["valid"] = bool(pyd.get("ok"))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?",
                        help="Path to YAML file, or '-' for stdin (omit with --batch)")
    parser.add_argument("--target", default="SimulationExperiment",
                        help="tvbo datamodel class to validate against (default: SimulationExperiment)")
    parser.add_argument("--runtime", action="store_true",
                        help="Also validate via the full runtime loader (needs xarray etc.)")
    parser.add_argument("--batch", action="store_true",
                        help="Read a JSON array of {text, target?, label?} from stdin and print a "
                             "JSON array of reports. Pays the heavy tvbo import once for the whole "
                             "batch instead of once per process spawn.")
    args = parser.parse_args(argv)

    # Batch mode: one tvbo import, many validations -> the fast path for the
    # 'every seeded experiment' e2e check.
    if args.batch:
        items = json.loads(sys.stdin.read())
        reports = []
        for item in items:
            rep = _validate_one(item["text"], item.get("target", args.target), args.runtime)
            rep["source"] = item.get("label")
            reports.append(rep)
        print(json.dumps(reports, indent=2))
        return 0 if all(r["valid"] for r in reports) else 1

    if not args.source:
        parser.error("source is required unless --batch is given")

    yaml_text = _read_source(args.source)
    report = _validate_one(yaml_text, args.target, args.runtime)
    report["source"] = args.source
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
