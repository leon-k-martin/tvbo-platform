# -*- coding: utf-8 -*-
"""Pre-migration: bridge schema shape changes before Odoo's auto schema sync.

This delegates to ``scripts/reconcile_schema.py`` — the single, version-
independent implementation of the schema bridges (rename via LinkML aliases,
free-text -> Many2one stash, Many2one -> scalar drop). The same reconciler is
run before every ``odoo -u tvbo`` by ``init-odoo.sh`` (so follow-latest schema
changes are handled even without a version bump); this hook is the belt-and-
suspenders copy for the version boundary and for deploys that bypass
``init-odoo.sh``. It is idempotent, so running both is harmless.

The enum *re-link* of stashed text (which needs the Odoo registry) stays in
``post-migrate.py``.
"""
import importlib.util
import logging
import os

_logger = logging.getLogger(__name__)

# Where the generated model layer lives, and where the reconciler may be found.
_MODELS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)


def _load_reconciler():
    """Locate and import scripts/reconcile_schema.py across layouts (image at
    /opt/tvbo, repo checkout, or an explicit TVBO_RECONCILE_PY)."""
    candidates = [os.environ.get("TVBO_RECONCILE_PY")]
    here = os.path.dirname(__file__)
    # repo layout: odoo-addons/tvbo/migrations/<ver>/ -> <repo>/scripts/
    candidates.append(os.path.normpath(
        os.path.join(here, "..", "..", "..", "..", "scripts", "reconcile_schema.py")))
    candidates += [
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
            "pre-migrate: reconcile_schema.py not found; relying on the boot-time "
            "reconciler (init-odoo.sh) to have bridged the schema already."
        )
        return
    summary = mod.reconcile(cr, _MODELS_DIR)
    _logger.info("pre-migrate: schema reconcile summary %s", summary)
