#!/usr/bin/env python3
"""Generate ``odoo-addons/tvbo/models/schema_models.py`` from the TVBO LinkML schema.

Thin wrapper around :class:`scripts.linkml_odoo_generator.OdooGenerator` (a
LinkML ``OOCodeGenerator`` subclass). One flow, one source of truth:

    tvbo/schema/tvbo_datamodel.yaml  --(SchemaView/OdooGenerator)-->  schema_models.py

Field names/types match ``tvbo.datamodel.pydantic`` because both come from the
same induced LinkML slots — no divergence to bridge.

(The previous 1000+-line hand-rolled generator, which also emitted views/menus/
access, is preserved at scripts/legacy/generate_odoo_models_legacy.py. Porting
view/menu/access generation onto this generator is a tracked follow-up.)

Usage:
    python scripts/generate_odoo_models.py [--schema PATH] [--out PATH] [--check]

``--check`` writes nothing and exits non-zero if the generated output differs
from the committed file (handy for CI).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "odoo-addons" / "tvbo" / "models" / "schema_models.py"


def _default_schema() -> Path:
    """Locate tvbo_datamodel.yaml across the layouts we may run in: a flat PyPI
    install (schema shipped as package data), an editable checkout (extra nesting
    level), or a /tmp mount. Mirrors building_blocks_api._locate_schema_file so
    build-time generation resolves the same ground truth the runtime API does."""
    candidates = []
    try:
        import tvbo  # noqa: WPS433
        pkg = Path(tvbo.__file__).resolve().parent
        candidates.append(pkg / "schema" / "tvbo_datamodel.yaml")          # flat PyPI install
        candidates.append(pkg.parent / "schema" / "tvbo_datamodel.yaml")   # editable checkout
    except Exception:  # noqa: BLE001
        pass
    candidates += [
        Path("/tmp/tvbo/schema/tvbo_datamodel.yaml"),
        Path("/tmp/tvbo/tvbo/schema/tvbo_datamodel.yaml"),
        Path("/tvbo/schema/tvbo_datamodel.yaml"),
        REPO.parent / "tvbo" / "schema" / "tvbo_datamodel.yaml",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    raise FileNotFoundError(
        "tvbo_datamodel.yaml not found (tried tvbo package data, /tmp/tvbo, "
        "sibling checkout); pass --schema explicitly."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true",
                        help="Exit non-zero if generated output differs from --out (writes nothing).")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from linkml_odoo_generator import OdooGenerator

    schema = args.schema or _default_schema()
    code = OdooGenerator(str(schema)).serialize()

    # Both artifacts live under the same addon root, derived from --out:
    #   <addon>/models/schema_models.py   and   <addon>/security/ir.model.access.csv
    # so a single --out fully controls where generation lands (build-time gen
    # points it at /mnt/extra-addons/tvbo; the default targets the repo).
    access = args.out.resolve().parent.parent / "security" / "ir.model.access.csv"
    access_csv = _access_csv_content(code)

    if args.check:
        cur_code = args.out.read_text() if args.out.is_file() else ""
        cur_csv = access.read_text() if access.is_file() else ""
        stale = []
        if cur_code != code:
            stale.append(str(args.out))
        if cur_csv != access_csv:
            stale.append(str(access))
        if stale:
            print("OUT OF DATE: differs from generated output:\n  "
                  + "\n  ".join(stale), file=sys.stderr)
            return 1
        print(f"OK: {args.out} and {access} are up to date.")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(code)
    n_models = code.count("(models.Model)")
    print(f"Wrote {n_models} Odoo models to {args.out} (from {schema})")

    # Regenerate ir.model.access.csv so every generated model has an access rule.
    access.parent.mkdir(parents=True, exist_ok=True)
    access.write_text(access_csv)
    print(f"Wrote {access_csv.count(chr(10)) - 1} access rules to {access}")
    return 0


def _access_csv_content(models_code: str) -> str:
    """Build the ir.model.access.csv body (one rule per generated model)."""
    import re
    # Match only the model `_name` line (4-space indent), not _rec_name/_description.
    model_names = re.findall(r"^    _name = '([^']+)'", models_code, re.M)
    lines = ["id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink"]
    for m in model_names:
        ident = m.replace(".", "_")
        lines.append(f"access_{ident},{m},model_{ident},base.group_user,1,1,1,1")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
