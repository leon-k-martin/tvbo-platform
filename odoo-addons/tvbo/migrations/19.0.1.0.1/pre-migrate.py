# -*- coding: utf-8 -*-
"""Pre-migration: bridge enum fields that changed from free text to Many2one.

The LinkML-generated schema turned a number of formerly free-text columns
(``unit``, ``terminology``, ``domain``, ``distribution``, ``software``, …) into
``Many2one`` references to controlled-vocabulary ("enum") models. On an
existing database those columns still hold the old text (e.g. ``"mV"``), so
Odoo's automatic schema sync issues ``ALTER COLUMN ... TYPE int4`` and Postgres
aborts the whole upgrade with::

    psycopg2.errors.InvalidTextRepresentation:
        invalid input syntax for type integer: "mV"

To make the upgrade survive without losing data, we rename every conflicting
text column to ``<col>__legacy_txt`` *before* the schema sync runs. Odoo then
creates a clean, empty integer FK column, and ``post-migrate.py`` re-links the
stashed values to enum records (auditing anything it can't map).

At the ``pre`` stage the module's new models are not yet loaded into the
registry, so we discover the set of ``Many2one`` columns by statically parsing
the model source on disk. This keeps the migration correct as the schema
evolves, and covers *every* affected column rather than only the one that
happened to crash first.
"""
import ast
import logging
import os
import re

_logger = logging.getLogger(__name__)

LEGACY_SUFFIX = "__legacy_txt"
# Postgres character types we treat as "old free text that must be bridged".
CHAR_TYPES = frozenset(
    ("character varying", "character", "text", '"char"', "varchar", "bpchar")
)
_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _ident(name):
    """Validate and double-quote a SQL identifier (names come from our own
    source, but we never interpolate anything unvalidated into DDL)."""
    if not _IDENT_RE.match(name or ""):
        raise ValueError("unexpected SQL identifier: %r" % (name,))
    return '"%s"' % name


def _many2one_columns(models_dir):
    """Yield ``(table, column)`` for every stored Many2one field declared in
    the module's model files."""
    for fname in sorted(os.listdir(models_dir)):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        path = os.path.join(models_dir, fname)
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError):
            _logger.exception("enum-fk migration: cannot parse %s", path)
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            table = None
            m2o_cols = []
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                    continue
                target = stmt.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                # _name = 'tvbo.xxx'  ->  physical table 'tvbo_xxx'
                if (
                    target.id == "_name"
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)
                ):
                    table = stmt.value.value.replace(".", "_")
                # field = fields.Many2one(...)
                elif isinstance(stmt.value, ast.Call):
                    func = stmt.value.func
                    if isinstance(func, ast.Attribute) and func.attr == "Many2one":
                        m2o_cols.append(target.id)
            if table:
                for col in m2o_cols:
                    yield table, col


def migrate(cr, version):
    models_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "models")
    )
    if not os.path.isdir(models_dir):
        _logger.error("enum-fk migration: models dir not found at %s", models_dir)
        return

    stashed = 0
    seen = set()
    for table, column in _many2one_columns(models_dir):
        if (table, column) in seen:
            continue
        seen.add((table, column))

        # Is there an existing column of a character type to bridge?
        cr.execute(
            """
            SELECT data_type
              FROM information_schema.columns
             WHERE table_schema = current_schema()
               AND table_name = %s
               AND column_name = %s
            """,
            (table, column),
        )
        row = cr.fetchone()
        if not row:
            continue  # brand-new field: nothing to convert
        if row[0] not in CHAR_TYPES:
            continue  # already an int FK (or otherwise non-text): no conflict

        legacy = column + LEGACY_SUFFIX
        cr.execute(
            """
            SELECT 1
              FROM information_schema.columns
             WHERE table_schema = current_schema()
               AND table_name = %s
               AND column_name = %s
            """,
            (table, legacy),
        )
        if cr.fetchone():
            continue  # already stashed by an earlier (interrupted) run

        _logger.info(
            "enum-fk migration: stashing %s.%s (%s) -> %s",
            table, column, row[0], legacy,
        )
        cr.execute(
            "ALTER TABLE %s RENAME COLUMN %s TO %s"
            % (_ident(table), _ident(column), _ident(legacy))
        )
        stashed += 1

    _logger.info("enum-fk migration: pre-migrate stashed %s text column(s)", stashed)
