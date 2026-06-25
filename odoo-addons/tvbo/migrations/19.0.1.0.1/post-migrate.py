# -*- coding: utf-8 -*-
"""Post-migration: re-link the text values stashed by ``pre-migrate.py``.

For every ``<col>__legacy_txt`` column left behind by the pre-migration, we:

  1. resolve the model + the field's target enum model from the now-loaded
     registry;
  2. match each distinct legacy text value against the enum's ``name`` /
     ``technical_name`` (case-insensitive) and write the resulting FK id back
     into the new integer column;
  3. record any value we could *not* map into ``tvbo_enum_migration_unmatched``
     so nothing is silently lost (enum tables are seeded later via the ingest
     flow, so a value may simply not exist yet — it can be backfilled from the
     audit table afterwards);
  4. drop the temporary ``__legacy_txt`` column.

Each column is handled in its own savepoint: a problem with one never aborts
the rest of the upgrade.
"""
import logging
import re

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

LEGACY_SUFFIX = "__legacy_txt"
AUDIT_TABLE = "tvbo_enum_migration_unmatched"
# Enum lookup fields, in priority order, that a legacy text value might equal.
MATCH_FIELDS = ("name", "technical_name")
_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _ident(name):
    if not _IDENT_RE.match(name or ""):
        raise ValueError("unexpected SQL identifier: %r" % (name,))
    return '"%s"' % name


def _ensure_audit_table(cr):
    cr.execute(
        """
        CREATE TABLE IF NOT EXISTS %s (
            id            serial PRIMARY KEY,
            table_name    varchar NOT NULL,
            column_name   varchar NOT NULL,
            res_id        integer NOT NULL,
            legacy_value  text,
            migrated_at   timestamp DEFAULT now()
        )
        """
        % _ident(AUDIT_TABLE)
    )


def _legacy_columns(cr):
    cr.execute(
        r"""
        SELECT table_name, column_name
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name LIKE 'tvbo\_%%'
           AND column_name LIKE %s
        """,
        ("%" + LEGACY_SUFFIX,),
    )
    return cr.fetchall()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _ensure_audit_table(cr)

    # physical table -> model name (skip abstract/transient without a real table)
    table2model = {}
    for model_name in env.registry.models:
        model = env[model_name]
        if getattr(model, "_auto", False) and model._table:
            table2model.setdefault(model._table, model_name)

    total_linked = total_unmatched = 0

    for table, legacy_col in _legacy_columns(cr):
        orig_col = legacy_col[: -len(LEGACY_SUFFIX)]
        try:
            with cr.savepoint():
                linked, unmatched = _relink_one(
                    cr, env, table2model, table, legacy_col, orig_col
                )
                total_linked += linked
                total_unmatched += unmatched
                cr.execute(
                    "ALTER TABLE %s DROP COLUMN %s"
                    % (_ident(table), _ident(legacy_col))
                )
        except Exception:  # noqa: BLE001 - never let one column abort the upgrade
            _logger.exception(
                "enum-fk migration: failed to re-link %s.%s; leaving %s in place "
                "for manual review",
                table, orig_col, legacy_col,
            )

    _logger.info(
        "enum-fk migration: post-migrate linked %s value(s), audited %s unmapped",
        total_linked, total_unmatched,
    )


def _relink_one(cr, env, table2model, table, legacy_col, orig_col):
    model_name = table2model.get(table)
    comodel = None
    if model_name and orig_col in env[model_name]._fields:
        field = env[model_name]._fields[orig_col]
        if field.type == "many2one":
            comodel = field.comodel_name

    # Distinct, non-empty legacy values still present.
    cr.execute(
        "SELECT DISTINCT %s FROM %s WHERE %s IS NOT NULL AND %s <> ''"
        % (_ident(legacy_col), _ident(table), _ident(legacy_col), _ident(legacy_col))
    )
    values = [r[0] for r in cr.fetchall()]
    if not values:
        return 0, 0

    value_to_id = {}
    if comodel and comodel in env.registry.models:
        co = env[comodel]
        match_fields = [f for f in MATCH_FIELDS if f in co._fields]
        for val in values:
            rec = co.browse()
            for mf in match_fields:
                rec = co.search([(mf, "=ilike", val)], limit=1)
                if rec:
                    break
            if rec:
                value_to_id[val] = rec.id

    linked = 0
    for val, rec_id in value_to_id.items():
        cr.execute(
            "UPDATE %s SET %s = %%s WHERE %s = %%s"
            % (_ident(table), _ident(orig_col), _ident(legacy_col)),
            (rec_id, val),
        )
        linked += cr.rowcount

    unmatched_vals = [v for v in values if v not in value_to_id]
    unmatched_rows = 0
    if unmatched_vals:
        cr.execute(
            "INSERT INTO %s (table_name, column_name, res_id, legacy_value) "
            "SELECT %%s, %%s, id, %s FROM %s WHERE %s = ANY(%%s)"
            % (_ident(AUDIT_TABLE), _ident(legacy_col), _ident(table), _ident(legacy_col)),
            (table, orig_col, list(unmatched_vals)),
        )
        unmatched_rows = cr.rowcount
        _logger.warning(
            "enum-fk migration: %s.%s -> %s: %s value(s) unmapped (audited): %s",
            table, orig_col, comodel or "?", len(unmatched_vals),
            sorted(unmatched_vals)[:20],
        )

    return linked, unmatched_rows
