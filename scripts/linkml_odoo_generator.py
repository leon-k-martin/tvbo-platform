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
* **Integers** -> the emitted ``BigInteger`` (int8), since LinkML integers are unbounded.
* **Multivalued primitives** -> Text (newline-joined; ``pydantic_loader`` splits
  them back to a list on read).
* **Reserved Odoo names** (the record API, e.g. ``id``, ``env``, ``copy``, and the log-access columns) get a ``record_`` prefix, except ``modified`` -> ``is_modified``; the emitted ``RENAMED_SLOTS`` maps each renamed slot to its field for the platform's ingest and export.

Run via :mod:`generate_odoo_models` (thin CLI wrapper).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from linkml.generators.oocodegen import OOCodeGenerator
from linkml_runtime.linkml_model.meta import ClassDefinition, SlotDefinition
from linkml_runtime.utils.formatutils import camelcase, underscore

# LinkML type *base* (or type name) -> constructor of the Odoo scalar field.
_SCALAR_MAP = {
    "str": "fields.Char", "string": "fields.Char",
    "int": "BigInteger", "integer": "BigInteger",
    "float": "fields.Float", "double": "fields.Float", "decimal": "fields.Float", "Decimal": "fields.Float",
    "bool": "fields.Boolean", "boolean": "fields.Boolean",
    "XSDDate": "fields.Date", "date": "fields.Date",
    "XSDDateTime": "fields.Datetime", "datetime": "fields.Datetime",
    "URIorCURIE": "fields.Char", "URI": "fields.Char", "Uri": "fields.Char", "Uriorcurie": "fields.Char",
    "Curie": "fields.Char", "NCName": "fields.Char", "Ncname": "fields.Char",
    "XSDTime": "fields.Char", "time": "fields.Char",
}

# Slot code-names that should always be a Text (multiline) field.
_TEXT_SLOTS = {"description"}

# Odoo 19's public record API plus its log-access columns: a field named after one of these shadows the ORM (``env`` breaks every record).
_ODOO_RESERVED = frozenset("""
    action_archive action_unarchive browse check_access check_access_rights check_access_rule check_field_access_rights concat copy copy_data
    copy_translations create default_get display_name ensure_one env exists export_data fetch fields_get filtered filtered_domain flush_model
    flush_recordset get_base_url get_external_id get_field_translations get_metadata get_property_definition grouped has_access id ids init
    invalidate_model invalidate_recordset is_transient load lock_for_update mapped modified name_create name_search new onchange read
    read_group search search_count search_fetch search_read sorted sudo toggle_active try_lock_for_update union unlink update
    update_field_translations with_company with_context with_env with_prefetch with_user write create_uid create_date write_uid write_date
""".split())


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
        if name == "modified":
            return "is_modified"  # column name predating the general rule
        return f"record_{name}" if name in _ODOO_RESERVED else name

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
    def _default_clause(slot: SlotDefinition, ctor: str) -> str:
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
        if raw in ("true", "false") and ctor == "fields.Boolean":
            return f", default={raw == 'true'}"
        return ""

    # ---- field generation ------------------------------------------------
    def _odoo_scalar(self, range_name: str, field_name: str) -> str:
        if field_name in _TEXT_SLOTS:
            return "fields.Text"
        t = self.schemaview.get_type(range_name)
        base = (t.base if t else None) or range_name
        return _SCALAR_MAP.get(base) or _SCALAR_MAP.get(range_name) or "fields.Char"

    def _field_definition(self, slot: SlotDefinition, model_snake: str) -> str:
        sv = self.schemaview
        name = self._field_name(slot)
        rng = slot.range or sv.schema.default_range or "string"

        slot_name = slot.alias or slot.name
        attrs = f", string={slot_name.replace('_', ' ').capitalize()!r}" if name != underscore(slot_name) else ""  # a renamed field keeps its slot's label
        if slot.description:
            attrs += f", help={slot.description.strip()!r}"

        # 'Any' literal holder (e.g. ScalarValue) -> Json, never a relation.
        if rng in self._any_classes():
            inner = attrs[2:] if attrs else ""
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
                return f"{name} = fields.Many2many(comodel_name='{comodel}', relation='{rel}'{cols}{attrs})"
            return f"{name} = fields.Many2one(comodel_name='{comodel}'{attrs})"

        # Enum -> lookup-model reference (Many2one/Many2many).
        if rng in sv.all_enums():
            comodel = self._model_name(rng)
            if slot.multivalued:
                rel = self._rel_table(model_snake, name)
                return f"{name} = fields.Many2many(comodel_name='{comodel}', relation='{rel}'{attrs})"
            return f"{name} = fields.Many2one(comodel_name='{comodel}'{attrs})"

        # Multivalued primitive -> Text blob (pydantic_loader splits to a list).
        if slot.multivalued:
            inner = attrs[2:] if attrs else ""
            return f"{name} = fields.Text({inner})"

        # Single primitive.
        ctor = self._odoo_scalar(rng, name)
        required = ", required=True" if slot.required else ""
        index = ", index=True" if name in ("name", "label") else ""
        default = self._default_clause(slot, ctor)
        inner = f"{required}{index}{default}{attrs}".lstrip(", ")
        return f"{name} = {ctor}({inner})"

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
            "class BigInteger(fields.Integer):",
            '    """LinkML integers are unbounded; int8 keeps values such as file sizes in bytes that overflow Odoo\'s int4."""',
            "",
            "    _column_type = ('int8', 'int8')",
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
        slot_names = sorted({underscore(s.alias or s.name) for s in sv.all_slots().values()})
        renamed = {n: field for n in slot_names if (field := self._normalize_name(n)) != n}
        parts.append(f"# Schema slots renamed away from Odoo's record API (slot -> field).\nRENAMED_SLOTS = {renamed!r}")
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
