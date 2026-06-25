# -*- coding: utf-8 -*-
"""Post-migration: re-link enum text stashed by the pre phase.

Delegates to ``scripts/reconcile_schema.py`` (``reconcile_post``) — the single,
version-independent implementation. The same step is run after every
``odoo -u tvbo`` by ``init-odoo.sh`` (``--phase post``), so follow-latest schema
changes are re-linked without a version bump; this hook is the belt-and-
suspenders copy for the version boundary and for deploys that bypass
``init-odoo.sh``. It is idempotent, so running both is harmless.

At the ``post`` stage Odoo has already created the fresh integer FK columns, so
the reconciler can match each ``<col>__legacy_txt`` value to an enum record and
write the FK id back (resolving the comodel from the generated ``comodel_name=``,
no registry needed), auditing anything unmatched into
``tvbo_enum_migration_unmatched`` before dropping the legacy column.
"""
import importlib.util
import logging
import os

_logger = logging.getLogger(__name__)

_MODELS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)


def _load_reconciler():
    """Locate and import scripts/reconcile_schema.py across layouts (image at
    /opt/tvbo, repo checkout, or an explicit TVBO_RECONCILE_PY)."""
    here = os.path.dirname(__file__)
    candidates = [
        os.environ.get("TVBO_RECONCILE_PY"),
        os.path.normpath(os.path.join(
            here, "..", "..", "..", "..", "scripts", "reconcile_schema.py")),
        "/opt/tvbo/reconcile_schema.py",
        "/opt/tvbo-scripts/reconcile_schema.py",
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            spec = importlib.util.spec_from_file_location("tvbo_reconcile_schema", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def migrate(cr, version):
    mod = _load_reconciler()
    if mod is None:
        _logger.warning(
            "post-migrate: reconcile_schema.py not found; relying on the boot-time "
            "reconciler (init-odoo.sh --phase post) to have re-linked enum text."
        )
        return
    summary = mod.reconcile_post(cr, _MODELS_DIR)
    _logger.info("post-migrate: schema reconcile (post) summary %s", summary)
