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
    # Prefer the installed tvbo package's schema; fall back to a sibling checkout.
    try:
        import tvbo  # noqa: WPS433
        cand = Path(tvbo.__file__).resolve().parent.parent / "schema" / "tvbo_datamodel.yaml"
        if cand.is_file():
            return cand
    except Exception:  # noqa: BLE001
        pass
    for cand in (
        Path("/Users/leonmartin_bih/tools/tvbo/schema/tvbo_datamodel.yaml"),
        REPO.parent / "tvbo" / "schema" / "tvbo_datamodel.yaml",
    ):
        if cand.is_file():
            return cand
    raise FileNotFoundError("tvbo_datamodel.yaml not found; pass --schema")


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

    if args.check:
        current = args.out.read_text() if args.out.is_file() else ""
        if current != code:
            print(f"OUT OF DATE: {args.out} differs from generated output.", file=sys.stderr)
            return 1
        print(f"OK: {args.out} is up to date.")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(code)
    n_models = code.count("(models.Model)")
    print(f"Wrote {n_models} Odoo models to {args.out} (from {schema})")

    # Regenerate ir.model.access.csv so every generated model has an access rule.
    _write_access_csv(code)
    return 0


def _write_access_csv(models_code: str) -> None:
    import re
    access = REPO / "odoo-addons" / "tvbo" / "security" / "ir.model.access.csv"
    # Match only the model `_name` line (4-space indent), not _rec_name/_description.
    model_names = re.findall(r"^    _name = '([^']+)'", models_code, re.M)
    lines = ["id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink"]
    for m in model_names:
        ident = m.replace(".", "_")
        lines.append(f"access_{ident},{m},model_{ident},base.group_user,1,1,1,1")
    access.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(model_names)} access rules to {access}")


if __name__ == "__main__":
    raise SystemExit(main())
