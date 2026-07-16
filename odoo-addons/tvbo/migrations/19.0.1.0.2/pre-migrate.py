# -*- coding: utf-8 -*-
"""Pre-migration: introduce the publication workflow on tvbo.model_share.

Before this version, ``tvbo.model_share.visibility`` was a plain, directly-
writable Selection (``private``/``shared``) that acted as the instant publish
toggle. This version turns publishing into a gated workflow: ``publication_state``
becomes the source of truth and ``visibility`` becomes a *computed* mirror
(``shared`` iff ``published``).

If we let Odoo add the new ``publication_state`` column with its ``draft``
default and then recompute ``visibility``, every previously-shared element would
silently fall back to ``private`` and vanish from the community gallery. To avoid
that data-visibility regression we backfill here, in the ``pre`` phase, while the
old ``visibility`` column still holds its real values and *before* Odoo loads the
new field definitions. Creating the columns ourselves (already populated) means
Odoo's schema sync adopts them as-is and never applies the default over our data.

Idempotent: guarded by information_schema checks and ``IS NULL`` predicates.
"""
import logging

_logger = logging.getLogger(__name__)

_TABLE = "tvbo_model_share"


def _column_exists(cr, column):
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s",
        (_TABLE, column),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    # If the platform table isn't there yet (very first install), nothing to do.
    cr.execute("SELECT to_regclass(%s)", (_TABLE,))
    if not cr.fetchone()[0]:
        return

    # 1. publication_state — the new source of truth. shared -> published.
    if not _column_exists(cr, "publication_state"):
        cr.execute("ALTER TABLE %s ADD COLUMN publication_state varchar" % _TABLE)
    cr.execute(
        "UPDATE {t} SET publication_state = "
        "CASE WHEN visibility = 'shared' THEN 'published' ELSE 'draft' END "
        "WHERE publication_state IS NULL".format(t=_TABLE)
    )

    # 2. validation_state — grandfather already-published elements as passed.
    if not _column_exists(cr, "validation_state"):
        cr.execute("ALTER TABLE %s ADD COLUMN validation_state varchar" % _TABLE)
    cr.execute(
        "UPDATE {t} SET validation_state = 'passed' "
        "WHERE publication_state = 'published' AND validation_state IS NULL".format(t=_TABLE)
    )
    cr.execute(
        "UPDATE {t} SET validation_state = 'not_run' "
        "WHERE validation_state IS NULL".format(t=_TABLE)
    )

    # 3. published_date — approximate with the last write for grandfathered rows.
    if not _column_exists(cr, "published_date"):
        cr.execute("ALTER TABLE %s ADD COLUMN published_date timestamp" % _TABLE)
    cr.execute(
        "UPDATE {t} SET published_date = write_date "
        "WHERE publication_state = 'published' AND published_date IS NULL".format(t=_TABLE)
    )

    cr.execute(
        "SELECT publication_state, count(*) FROM {t} GROUP BY publication_state".format(t=_TABLE)
    )
    _logger.info("pre-migrate 19.0.1.0.2: publication_state backfill -> %s", dict(cr.fetchall()))
