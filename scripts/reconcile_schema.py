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

Four bridges across two phases, all derived from the generated model source on
disk (no Odoo registry needed) and safe to re-run.

PRE phase (``reconcile_pre``, before ``-u tvbo``):

1. **rename** — a slot renamed in the schema keeps its old name(s) as LinkML
   ``aliases``; the generator emits these as ``_FIELD_ALIASES``. For each
   ``(model, new_col) -> [old_col, ...]`` where the DB still has ``old_col`` but
   not ``new_col``, ``RENAME COLUMN old_col TO new_col`` so data survives.

2. **enum-stash** (free text -> Many2one) — a column that became a Many2one but
   still holds old free text (e.g. ``"mV"``) is renamed to ``<col>__legacy_txt``
   so Odoo creates a clean integer FK column instead of aborting on
   ``invalid input syntax for type integer``.

3. **reverse-fk-drop** (Many2one -> scalar) — a former Many2one (integer column
   with a FK) that is now a non-relational scalar is dropped, so Odoo recreates
   it fresh instead of aborting while re-validating the FK against an
   incompatible type. The stored integer is a dead FK id, meaningless as the new
   type.

POST phase (``reconcile_post``, after ``-u tvbo`` has created the fresh FK column):

4. **enum-relink** — match each ``<col>__legacy_txt`` value against the target
   enum's ``name`` / ``technical_name`` (comodel resolved from the generated
   ``comodel_name=``, so no Odoo registry is needed), write the FK id back into
   the new column, audit anything unmatched into ``tvbo_enum_migration_unmatched``,
   then drop the legacy column. This was previously a version-gated
   ``post-migrate.py`` step; running it here makes it fire on every upgrade.

Run standalone (init-odoo.sh runs --phase pre before -u tvbo, --phase post after):
    python3 reconcile_schema.py --phase pre  --models-dir DIR --db-host H ... [--dry-run]
    python3 reconcile_schema.py --phase post --models-dir DIR --db-host H ... [--dry-run]

Or call ``reconcile_pre(cr, models_dir)`` / ``reconcile_post(cr, models_dir)``
with any DB-API cursor (e.g. Odoo's ``cr``).
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
# Enum lookup fields (in priority order) a stashed legacy text value may equal,
# and the audit table for values that cannot be matched (relink phase).
MATCH_FIELDS = ("name", "technical_name")
AUDIT_TABLE = "tvbo_enum_migration_unmatched"
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


def _enum_comodels(models_dir):
    """Map ``(table, column) -> comodel_table`` for every Many2one, read from the
    generated ``comodel_name=`` kwarg. Lets the relink phase resolve an enum
    target without the Odoo registry."""
    out = {}
    for path in _model_files(models_dir):
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError):
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            table = None
            m2o = []
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
                elif (
                    isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and stmt.value.func.attr == "Many2one"
                ):
                    for kw in stmt.value.keywords:
                        if (
                            kw.arg == "comodel_name"
                            and isinstance(kw.value, ast.Constant)
                            and isinstance(kw.value.value, str)
                        ):
                            m2o.append((target.id, kw.value.value.replace(".", "_")))
            if table:
                for col, comodel in m2o:
                    out[(table, col)] = comodel
    return out


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


def _ensure_audit_table(cr, dry_run):
    _ddl(
        cr,
        "CREATE TABLE IF NOT EXISTS %s ("
        " id serial PRIMARY KEY,"
        " table_name varchar NOT NULL,"
        " column_name varchar NOT NULL,"
        " res_id integer NOT NULL,"
        " legacy_value text,"
        " migrated_at timestamp DEFAULT now())" % _ident(AUDIT_TABLE),
        dry_run,
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


def _relink_one(cr, table, legacy_col, orig, comodel, dry_run):
    cr.execute(
        "SELECT DISTINCT %s FROM %s WHERE %s IS NOT NULL AND %s <> ''"
        % (_ident(legacy_col), _ident(table), _ident(legacy_col), _ident(legacy_col))
    )
    values = [r[0] for r in cr.fetchall()]
    if not values:
        return 0, 0

    mapped = {}
    if comodel and _column_type(cr, comodel, "id") is not None:
        match_fields = [f for f in MATCH_FIELDS if _column_type(cr, comodel, f) is not None]
        for val in values:
            for mf in match_fields:
                cr.execute(
                    "SELECT id FROM %s WHERE lower(%s) = lower(%%s) LIMIT 1"
                    % (_ident(comodel), _ident(mf)),
                    (val,),
                )
                row = cr.fetchone()
                if row:
                    mapped[val] = row[0]
                    break

    linked = 0
    for val, rec_id in mapped.items():
        if dry_run:
            _logger.info("reconcile relink [dry-run]: %s.%s = %s WHERE %s=%r",
                         table, orig, rec_id, legacy_col, val)
            linked += 1
            continue
        cr.execute(
            "UPDATE %s SET %s = %%s WHERE %s = %%s"
            % (_ident(table), _ident(orig), _ident(legacy_col)),
            (rec_id, val),
        )
        linked += cr.rowcount

    unmatched_vals = [v for v in values if v not in mapped]
    if unmatched_vals and not dry_run:
        cr.execute(
            "INSERT INTO %s (table_name, column_name, res_id, legacy_value) "
            "SELECT %%s, %%s, id, %s FROM %s WHERE %s = ANY(%%s)"
            % (_ident(AUDIT_TABLE), _ident(legacy_col), _ident(table), _ident(legacy_col)),
            (table, orig, list(unmatched_vals)),
        )
    if unmatched_vals:
        _logger.warning(
            "reconcile relink: %s.%s -> %s: %s value(s) unmapped (audited): %s",
            table, orig, comodel or "?", len(unmatched_vals), sorted(unmatched_vals)[:20],
        )
    return linked, len(unmatched_vals)


def _relink_pass(cr, models_dir, dry_run):
    """Re-link text stashed as ``<col>__legacy_txt`` to enum FK ids, then drop the
    legacy column. Runs AFTER Odoo creates the fresh integer FK column. Each
    column is handled in its own savepoint so one failure never aborts the rest."""
    legacy = _legacy_columns(cr)
    if not legacy:
        _logger.info("reconcile relink: no __legacy_txt columns to re-link")
        return {"linked": 0, "unmatched": 0}
    comodels = _enum_comodels(models_dir)
    linked = unmatched = 0
    audit_ready = False
    for table, legacy_col in legacy:
        orig = legacy_col[: -len(LEGACY_SUFFIX)]
        # The fresh FK column must exist (Odoo creates it during -u); otherwise
        # leave the legacy column in place and re-link on a later run.
        if _column_type(cr, table, orig) is None:
            _logger.info(
                "reconcile relink: %s.%s not created yet; keeping %s for next run",
                table, orig, legacy_col,
            )
            continue
        cr.execute("SAVEPOINT reconcile_relink")
        try:
            if not audit_ready:
                _ensure_audit_table(cr, dry_run)
                audit_ready = True
            l, u = _relink_one(cr, table, legacy_col, orig, comodels.get((table, orig)), dry_run)
            linked += l
            unmatched += u
            _ddl(cr, "ALTER TABLE %s DROP COLUMN %s" % (_ident(table), _ident(legacy_col)), dry_run)
            cr.execute("RELEASE SAVEPOINT reconcile_relink")
        except Exception:  # noqa: BLE001 - never let one column abort the rest
            cr.execute("ROLLBACK TO SAVEPOINT reconcile_relink")
            _logger.exception(
                "reconcile relink: failed on %s.%s; leaving %s for manual review",
                table, orig, legacy_col,
            )
    _logger.info("reconcile relink: linked %s value(s), audited %s unmatched", linked, unmatched)
    return {"linked": linked, "unmatched": unmatched}


def reconcile_pre(cr, models_dir, dry_run=False):
    """Bridges to run BEFORE ``-u tvbo`` (idempotent). Order matters: rename via
    aliases first (so later passes see the new column name), then enum-stash,
    then reverse-fk-drop."""
    if not os.path.isdir(models_dir):
        _logger.error("reconcile: models dir not found at %s", models_dir)
        return {"renamed": 0, "stashed": 0, "dropped": 0}
    return {
        "renamed": _rename_pass(cr, models_dir, dry_run),
        "stashed": _enum_stash_pass(cr, models_dir, dry_run),
        "dropped": _reverse_fk_pass(cr, models_dir, dry_run),
    }


def reconcile_post(cr, models_dir, dry_run=False):
    """Bridge to run AFTER ``-u tvbo`` (idempotent): re-link stashed enum text to
    the fresh FK columns Odoo just created."""
    if not os.path.isdir(models_dir):
        _logger.error("reconcile: models dir not found at %s", models_dir)
        return {"linked": 0, "unmatched": 0}
    return _relink_pass(cr, models_dir, dry_run)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-host", default=os.environ.get("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.environ.get("DB_PORT", "5432"))
    parser.add_argument("--db-user", default=os.environ.get("DB_USER", "odoo"))
    parser.add_argument("--db-password", default=os.environ.get("DB_PASSWORD", "odoo"))
    parser.add_argument("--db-name", default=os.environ.get("DB_NAME", "tvbo"))
    parser.add_argument("--models-dir", required=True,
                        help="Path to the generated Odoo models dir (has schema_models.py).")
    parser.add_argument("--phase", choices=("pre", "post"), default="pre",
                        help="'pre' (before -u tvbo): rename/stash/drop. "
                             "'post' (after -u tvbo): re-link stashed enum text.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Log intended DDL without executing it.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    import psycopg2  # local import: only needed for standalone runs
    conn = psycopg2.connect(
        host=args.db_host, port=args.db_port, user=args.db_user,
        password=args.db_password, dbname=args.db_name,
    )
    run = reconcile_post if args.phase == "post" else reconcile_pre
    try:
        with conn.cursor() as cr:
            summary = run(cr, args.models_dir, dry_run=args.dry_run)
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
