#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconcile the live Odoo DB schema to the generated tvbo model layer.

Under "follow-latest" the Odoo addon's models are regenerated from the tvbo
LinkML ground truth on every image build, but the addon *version* does not
change. Odoo only runs version-gated ``migrations/<version>/`` scripts when the
installed version is below the manifest version, so those scripts cannot bridge
schema changes that arrive without a version bump. This module is the
version-INDEPENDENT counterpart: it is run before every ``odoo -u tvbo`` (see
``init-odoo.sh``) and applies the idempotent, crash-preventing bridges that
Odoo's automatic ``ALTER COLUMN`` schema sync cannot do on its own.

Three passes, all derived from the generated model source on disk (no Odoo
registry needed) and safe to re-run:

1. **rename** — a slot renamed in the schema keeps its old name(s) as LinkML
   ``aliases``; the generator emits these as ``_FIELD_ALIASES``. For each
   ``(model, new_col) -> [old_col, ...]`` where the DB still has ``old_col`` but
   not ``new_col``, ``RENAME COLUMN old_col TO new_col`` so data survives.

2. **enum-stash** (free text -> Many2one) — a column that became a Many2one but
   still holds old free text (e.g. ``"mV"``) is renamed to ``<col>__legacy_txt``
   so Odoo creates a clean integer FK column instead of aborting on
   ``invalid input syntax for type integer``. The version-gated
   ``post-migrate.py`` re-links the stashed text to enum records (needs the Odoo
   registry, so it stays there; data is preserved meanwhile).

3. **reverse-fk-drop** (Many2one -> scalar) — a former Many2one (integer column
   with a FK) that is now a non-relational scalar is dropped, so Odoo recreates
   it fresh instead of aborting while re-validating the FK against an
   incompatible type. The stored integer is a dead FK id, meaningless as the new
   type.

Run standalone:
    python3 reconcile_schema.py --db-host H --db-user U --db-password P \
        --db-name tvbo --models-dir /mnt/extra-addons/tvbo/models [--dry-run]

Or call ``reconcile(cr, models_dir)`` with any DB-API cursor (e.g. Odoo's ``cr``).
"""
import argparse
import ast
import logging
import os
import re
import sys

_logger = logging.getLogger("tvbo.reconcile_schema")

LEGACY_SUFFIX = "__legacy_txt"
CHAR_TYPES = frozenset(
    ("character varying", "character", "text", '"char"', "varchar", "bpchar")
)
INT_TYPES = frozenset(("integer", "bigint", "smallint"))
# Field constructors that legitimately keep an integer column (or manage their
# own FK), so a former-Many2one column must NOT be dropped for them.
KEEP_INT_FIELDS = frozenset(("Many2one", "Many2many", "One2many", "Integer"))
_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _ident(name):
    """Validate and double-quote a SQL identifier. Names come from our own model
    source / schema, but never interpolate anything unvalidated into DDL."""
    if not _IDENT_RE.match(name or ""):
        raise ValueError("unexpected SQL identifier: %r" % (name,))
    return '"%s"' % name


# ---- static model introspection (no Odoo registry) ----------------------

def _model_files(models_dir):
    for fname in sorted(os.listdir(models_dir)):
        if fname.endswith(".py") and fname != "__init__.py":
            yield os.path.join(models_dir, fname)


def _declared_fields(models_dir):
    """Yield ``(table, column, ctor)`` for every ``fields.<Ctor>(...)`` declared
    in the model files, where ``ctor`` is e.g. ``Many2one`` / ``Text``."""
    for path in _model_files(models_dir):
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError):
            _logger.exception("reconcile: cannot parse %s", path)
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            table = None
            cols = []
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                    continue
                target = stmt.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                if (
                    target.id == "_name"
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str)
                ):
                    table = stmt.value.value.replace(".", "_")
                elif isinstance(stmt.value, ast.Call):
                    func = stmt.value.func
                    if isinstance(func, ast.Attribute):
                        cols.append((target.id, func.attr))
            if table:
                for col, ctor in cols:
                    yield table, col, ctor


def _field_aliases(models_dir):
    """Read the generated ``_FIELD_ALIASES`` map
    ``{(model, new_col): [old_col, ...]}`` from the model source. Returns {} if
    absent (a generation predating alias emission)."""
    for path in _model_files(models_dir):
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError):
            continue
        for node in tree.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "_FIELD_ALIASES"
            ):
                try:
                    return ast.literal_eval(node.value)
                except (ValueError, SyntaxError, TypeError):
                    _logger.exception("reconcile: cannot parse _FIELD_ALIASES in %s", path)
                    return {}
    return {}


# ---- DB introspection ----------------------------------------------------

def _column_type(cr, table, column):
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
    return row[0] if row else None


def _fk_constraints_on(cr, table, column):
    cr.execute(
        """
        SELECT con.conname
          FROM pg_constraint con
          JOIN pg_class rel ON rel.oid = con.conrelid
          JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
         WHERE con.contype = 'f'
           AND nsp.nspname = current_schema()
           AND rel.relname = %s
           AND EXISTS (
               SELECT 1 FROM pg_attribute att
                WHERE att.attrelid = con.conrelid
                  AND att.attnum = ANY (con.conkey)
                  AND att.attname = %s
           )
        """,
        (table, column),
    )
    return [r[0] for r in cr.fetchall()]


def _ddl(cr, sql, dry_run):
    if dry_run:
        _logger.info("reconcile [dry-run]: %s", sql)
        return
    cr.execute(sql)


# ---- passes --------------------------------------------------------------

def _rename_pass(cr, models_dir, dry_run):
    """Carry data across slots renamed via LinkML aliases."""
    aliases = _field_aliases(models_dir)
    renamed = 0
    for (model, new_col), old_cols in sorted(aliases.items()):
        table = model.replace(".", "_")
        if _column_type(cr, table, new_col) is not None:
            continue  # new column already present: nothing to carry over
        for old_col in old_cols:
            if old_col == new_col or _column_type(cr, table, old_col) is None:
                continue
            _logger.info(
                "reconcile rename: %s.%s -> %s (LinkML alias); renaming to preserve data",
                table, old_col, new_col,
            )
            _ddl(
                cr,
                "ALTER TABLE %s RENAME COLUMN %s TO %s"
                % (_ident(table), _ident(old_col), _ident(new_col)),
                dry_run,
            )
            renamed += 1
            break  # first matching old name wins
    _logger.info("reconcile rename: %s column(s) renamed", renamed)
    return renamed


def _enum_stash_pass(cr, models_dir, dry_run):
    """Free text -> Many2one: stash old text to ``<col>__legacy_txt`` so Odoo
    builds a clean integer FK column (post-migrate re-links the text)."""
    stashed = 0
    seen = set()
    for table, column, ctor in _declared_fields(models_dir):
        if ctor != "Many2one" or (table, column) in seen:
            continue
        seen.add((table, column))
        data_type = _column_type(cr, table, column)
        if data_type is None or data_type not in CHAR_TYPES:
            continue
        legacy = column + LEGACY_SUFFIX
        if _column_type(cr, table, legacy) is not None:
            continue  # already stashed by an earlier run
        _logger.info("reconcile enum-stash: %s.%s (%s) -> %s", table, column, data_type, legacy)
        _ddl(
            cr,
            "ALTER TABLE %s RENAME COLUMN %s TO %s"
            % (_ident(table), _ident(column), _ident(legacy)),
            dry_run,
        )
        stashed += 1
    _logger.info("reconcile enum-stash: %s text column(s) stashed", stashed)
    return stashed


def _reverse_fk_pass(cr, models_dir, dry_run):
    """Many2one -> scalar: drop a former-FK integer column now declared
    non-relational, so Odoo recreates it fresh (the integer is a dead FK id)."""
    dropped = 0
    seen = set()
    for table, column, ctor in _declared_fields(models_dir):
        if ctor in KEEP_INT_FIELDS or (table, column) in seen:
            continue
        seen.add((table, column))
        if _column_type(cr, table, column) not in INT_TYPES:
            continue
        fks = _fk_constraints_on(cr, table, column)
        if not fks:
            continue  # plain integer (genuine value): leave it
        cr.execute(
            "SELECT count(*) FROM %s WHERE %s IS NOT NULL"
            % (_ident(table), _ident(column))
        )
        nonnull = cr.fetchone()[0]
        _logger.info(
            "reconcile reverse-fk: dropping former-FK column %s.%s "
            "(integer, now %s; constraint(s): %s; %s non-null row(s))",
            table, column, ctor, ", ".join(fks), nonnull,
        )
        _ddl(cr, "ALTER TABLE %s DROP COLUMN %s" % (_ident(table), _ident(column)), dry_run)
        dropped += 1
    _logger.info("reconcile reverse-fk: %s former-FK column(s) dropped", dropped)
    return dropped


def reconcile(cr, models_dir, dry_run=False):
    """Run all bridges against ``cr`` (any DB-API cursor). Idempotent.
    Order matters: rename first (so later passes act on the new column name),
    then enum-stash, then reverse-fk-drop."""
    if not os.path.isdir(models_dir):
        _logger.error("reconcile: models dir not found at %s", models_dir)
        return {"renamed": 0, "stashed": 0, "dropped": 0}
    return {
        "renamed": _rename_pass(cr, models_dir, dry_run),
        "stashed": _enum_stash_pass(cr, models_dir, dry_run),
        "dropped": _reverse_fk_pass(cr, models_dir, dry_run),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-host", default=os.environ.get("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.environ.get("DB_PORT", "5432"))
    parser.add_argument("--db-user", default=os.environ.get("DB_USER", "odoo"))
    parser.add_argument("--db-password", default=os.environ.get("DB_PASSWORD", "odoo"))
    parser.add_argument("--db-name", default=os.environ.get("DB_NAME", "tvbo"))
    parser.add_argument("--models-dir", required=True,
                        help="Path to the generated Odoo models dir (has schema_models.py).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log intended DDL without executing it.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    import psycopg2  # local import: only needed for standalone runs
    conn = psycopg2.connect(
        host=args.db_host, port=args.db_port, user=args.db_user,
        password=args.db_password, dbname=args.db_name,
    )
    try:
        with conn.cursor() as cr:
            summary = reconcile(cr, args.models_dir, dry_run=args.dry_run)
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    finally:
        conn.close()
    _logger.info("reconcile: done (%s)", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
