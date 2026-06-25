"""LinkML -> Odoo model generator.

A thin :class:`~linkml.generators.oocodegen.OOCodeGenerator` subclass that emits
``odoo-addons/tvbo/models/schema_models.py`` directly from the TVBO LinkML
schema. By using LinkML's ``SchemaView`` (induced slots, ranges, enums,
inheritance, aliases) instead of hand-rolled YAML walking, the generated Odoo
field names and types match ``tvbo.datamodel.pydantic`` *exactly* — there is no
divergence to bridge.

Design choices (see platform todo.md / the discussion that produced this):

* **Field names follow the slot's code name** (``alias or name``), exactly like
  ``gen-pydantic``/``gen-python``. So ``lhs``/``rhs`` (not ``lefthandside``).
* **Inheritance is flattened**: every class gets *all* its induced slots as
  direct Odoo fields (no ``_inherits`` delegation, no ``<parent>_id`` link).
  This mirrors the Pydantic models (Solver fields live inline on Integrator)
  and removes the old ``solver_id`` artifact.
* **Enums become lookup models** (``tvbo.<enum>`` with name/technical_name/
  description) referenced via Many2one/Many2many — matching the seeded enum data.
* **Class ranges** -> Many2one (single) / Many2many (multivalued).
* **Multivalued primitives** -> Text (newline-joined; ``pydantic_loader`` splits
  them back to a list on read).
* **Reserved Odoo names** are renamed: ``id`` -> ``record_id``,
  ``modified`` -> ``is_modified``.

Run via :mod:`generate_odoo_models` (thin CLI wrapper).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from linkml.generators.oocodegen import OOCodeGenerator
from linkml_runtime.linkml_model.meta import ClassDefinition, SlotDefinition
from linkml_runtime.utils.formatutils import camelcase, underscore

# LinkML type *base* (or type name) -> Odoo scalar field class.
_SCALAR_MAP = {
    "str": "Char", "string": "Char",
    "int": "Integer", "integer": "Integer",
    "float": "Float", "double": "Float", "decimal": "Float", "Decimal": "Float",
    "bool": "Boolean", "boolean": "Boolean",
    "XSDDate": "Date", "date": "Date",
    "XSDDateTime": "Datetime", "datetime": "Datetime",
    "URIorCURIE": "Char", "URI": "Char", "Uri": "Char", "Uriorcurie": "Char",
    "Curie": "Char", "NCName": "Char", "Ncname": "Char",
    "XSDTime": "Char", "time": "Char",
}

# Slot code-names that should always be a Text (multiline) field.
_TEXT_SLOTS = {"description"}

# Reserved Odoo ORM field names -> safe rename (mirrors the inverse used by the
# platform's experiment_to_schema_dict).
_RESERVED = {"id": "record_id", "modified": "is_modified"}


@dataclass
class OdooGenerator(OOCodeGenerator):
    generatorname = "odoo"
    generatorversion = "0.2.0"
    valid_formats = ["odoo"]
    file_extension = "py"
    uses_schemaloader = False

    # Required by the OOCodeGenerator ABC (unused: Odoo field defaults come from
    # ifabsent via _default_clause).
    def default_value_for_type(self, typ: str) -> str:
        return "False"

    _any_cache: set | None = None

    def _any_classes(self) -> set:
        """Classes that are really 'any literal' holders (``class_uri: linkml:Any``,
        e.g. ScalarValue). Slots ranging on these store a raw value, so they map
        to an Odoo Json field rather than a relation, and we don't emit a model."""
        if self._any_cache is None:
            self._any_cache = {
                cn for cn in self.schemaview.all_classes()
                if (self.schemaview.get_class(cn).class_uri or "") == "linkml:Any"
            }
        return self._any_cache

    # ---- naming helpers --------------------------------------------------
    @staticmethod
    def _snake(name: str) -> str:
        """CamelCase -> snake_case. Matches building_blocks_api._camel_to_snake
        so generated _name values line up with _class_to_odoo_model()."""
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @classmethod
    def _model_name(cls, class_name: str) -> str:
        return f"tvbo.{cls._snake(class_name)}"

    @staticmethod
    def _py_class(class_name: str) -> str:
        return camelcase(class_name)

    @staticmethod
    def _normalize_name(raw: str) -> str:
        """Slot/alias text -> Odoo column name (snake + reserved-word remap).
        Applied identically to a slot's current name and its historical aliases,
        so an alias resolves to the exact column a prior generation emitted."""
        name = underscore(raw)
        return _RESERVED.get(name, name)

    def _field_name(self, slot: SlotDefinition) -> str:
        return self._normalize_name(slot.alias or slot.name)

    def _rel_table(self, model_snake: str, field_name: str) -> str:
        """Odoo m2m relation table name, kept within Postgres' 63-char limit."""
        rel = f"tvbo_{model_snake}_{field_name}_rel"
        if len(rel) > 63:
            digest = hashlib.md5(rel.encode()).hexdigest()[:6]
            rel = f"{rel[:56]}_{digest}"
        return rel

    # ---- ifabsent / defaults --------------------------------------------
    @staticmethod
    def _default_clause(slot: SlotDefinition, odoo_type: str) -> str:
        raw = slot.ifabsent
        if not raw or not isinstance(raw, str):
            return ""
        m = re.match(r"^(int|float|string|boolean)\((.*)\)$", raw)
        if m:
            kind, val = m.group(1), m.group(2)
            if kind == "int":
                return f", default={int(val)}"
            if kind == "float":
                return f", default={float(val)}"
            if kind == "boolean":
                return f", default={val.strip().lower() == 'true'}"
            if kind == "string":
                return f", default={val!r}"
        if raw in ("true", "false") and odoo_type == "Boolean":
            return f", default={raw == 'true'}"
        return ""

    # ---- field generation ------------------------------------------------
    def _odoo_scalar(self, range_name: str, field_name: str) -> str:
        if field_name in _TEXT_SLOTS:
            return "Text"
        t = self.schemaview.get_type(range_name)
        base = (t.base if t else None) or range_name
        return _SCALAR_MAP.get(base) or _SCALAR_MAP.get(range_name) or "Char"

    def _field_definition(self, slot: SlotDefinition, model_snake: str) -> str:
        sv = self.schemaview
        name = self._field_name(slot)
        rng = slot.range or sv.schema.default_range or "string"

        help_clause = ""
        if slot.description:
            help_clause = f", help={slot.description.strip()!r}"

        # 'Any' literal holder (e.g. ScalarValue) -> Json, never a relation.
        if rng in self._any_classes():
            inner = help_clause[2:] if help_clause else ""
            return f"{name} = fields.Json({inner})"

        # Class reference -> relational field.
        if rng in sv.all_classes():
            comodel = self._model_name(rng)
            if slot.multivalued:
                rel = self._rel_table(model_snake, name)
                self_ref = comodel == f"tvbo.{model_snake}"
                cols = (
                    f", column1='{model_snake}_id', column2='{name}_id'" if self_ref else ""
                )
                return f"{name} = fields.Many2many(comodel_name='{comodel}', relation='{rel}'{cols}{help_clause})"
            return f"{name} = fields.Many2one(comodel_name='{comodel}'{help_clause})"

        # Enum -> lookup-model reference (Many2one/Many2many).
        if rng in sv.all_enums():
            comodel = self._model_name(rng)
            if slot.multivalued:
                rel = self._rel_table(model_snake, name)
                return f"{name} = fields.Many2many(comodel_name='{comodel}', relation='{rel}'{help_clause})"
            return f"{name} = fields.Many2one(comodel_name='{comodel}'{help_clause})"

        # Multivalued primitive -> Text blob (pydantic_loader splits to a list).
        if slot.multivalued:
            inner = help_clause[2:] if help_clause else ""
            return f"{name} = fields.Text({inner})"

        # Single primitive.
        odoo_type = self._odoo_scalar(rng, name)
        required = ", required=True" if slot.required else ""
        index = ", index=True" if name in ("name", "label") else ""
        default = self._default_clause(slot, odoo_type)
        inner = f"{required}{index}{default}{help_clause}".lstrip(", ")
        return f"{name} = fields.{odoo_type}({inner})"

    # ---- model generation ------------------------------------------------
    def _rec_name(self, field_names: list[str]) -> str | None:
        for candidate in ("name", "label", "title"):
            if candidate in field_names:
                return candidate
        return None

    def _enum_model(self, enum_name: str) -> str:
        py = self._py_class(enum_name)
        model = self._model_name(enum_name)
        return (
            f"class {py}(models.Model):\n"
            f"    _name = {model!r}\n"
            f"    _description = {enum_name!r}\n"
            f"    _rec_name = 'name'\n\n"
            f"    name = fields.Char(required=True, index=True)\n"
            f"    technical_name = fields.Char(required=True, index=True)\n"
            f"    description = fields.Text()\n"
        )

    def _class_model(self, class_name: str, cls: ClassDefinition) -> str:
        sv = self.schemaview
        py = self._py_class(class_name)
        model = self._model_name(class_name)
        model_snake = self._snake(class_name)
        desc = (cls.description or class_name).replace("\n", " ").strip()
        if len(desc) > 220:
            desc = desc[:217] + "..."

        # All induced slots (inheritance flattened, mirrors pydantic).
        field_lines: list[str] = []
        field_names: list[str] = []
        for slot in sv.class_induced_slots(class_name):
            try:
                line = self._field_definition(slot, model_snake)
            except Exception as exc:  # noqa: BLE001
                line = f"# SKIPPED slot {slot.name!r}: {exc}"
            field_names.append(self._field_name(slot))
            field_lines.append(f"    {line}")

        rec = self._rec_name(field_names)
        head = [
            f"class {py}(models.Model):",
            f"    _name = {model!r}",
            f"    _description = {desc!r}",
        ]
        if rec:
            head.append(f"    _rec_name = {rec!r}")
        body = field_lines or ["    pass"]
        return "\n".join(head) + "\n\n" + "\n".join(body) + "\n"

    def _alias_map(self) -> dict:
        """Map ``(model_name, new_column) -> [old_column, ...]`` from LinkML slot
        ``aliases``. A renamed slot keeps its former name(s) as aliases (e.g.
        ``nodes`` aliases ``regions``), so this records the rename lineage that
        migrations replay as ``RENAME COLUMN`` to carry data across renames."""
        sv = self.schemaview
        any_classes = self._any_classes()
        out = {}
        for class_name in sorted(sv.all_classes()):
            if class_name in any_classes:
                continue
            model = self._model_name(class_name)
            for slot in sv.class_induced_slots(class_name):
                aliases = getattr(slot, "aliases", None) or []
                if not aliases:
                    continue
                new = self._field_name(slot)
                seen = {new}
                olds = []
                for a in aliases:
                    old = self._normalize_name(a)
                    if old not in seen:
                        seen.add(old)
                        olds.append(old)
                if olds:
                    out[(model, new)] = olds
        return out

    # ---- entrypoint ------------------------------------------------------
    def serialize(self) -> str:
        sv = self.schemaview
        parts = [
            "# -*- coding: utf-8 -*-",
            "# Auto-generated from the TVBO LinkML schema - DO NOT EDIT MANUALLY.",
            "# Re-run: python scripts/generate_odoo_models.py",
            "from odoo import models, fields",
            "",
            "",
        ]

        # Rename lineage from LinkML slot `aliases`, consumed by migrations
        # (pre-migrate) to RENAME COLUMN and preserve data across schema renames.
        alias_map = self._alias_map()
        alias_lines = [
            "# Column renames recorded as LinkML slot `aliases`"
            " (new_column -> [old_columns]).",
            "# Migrations replay these as RENAME COLUMN so data survives slot renames.",
            "_FIELD_ALIASES = {",
        ]
        for key in sorted(alias_map):
            model, new = key
            alias_lines.append(f"    ({model!r}, {new!r}): {alias_map[key]!r},")
        alias_lines.append("}")
        parts.append("\n".join(alias_lines))
        parts.append("")
        for enum_name in sorted(sv.all_enums()):
            parts.append(self._enum_model(enum_name))
            parts.append("")
        any_classes = self._any_classes()
        for class_name in sorted(sv.all_classes()):
            if class_name in any_classes:
                continue  # 'Any' holder -> represented as Json on referencing fields
            parts.append(self._class_model(class_name, sv.get_class(class_name)))
            parts.append("")
        return "\n".join(parts).rstrip() + "\n"
