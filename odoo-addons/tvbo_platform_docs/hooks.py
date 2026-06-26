# -*- coding: utf-8 -*-
"""Install/upgrade hook for tvbo_platform_docs.

Importing the git Markdown into ``tvbo.doc.page`` on install (and on every
module update) keeps the DB copy in step with the shipped files without a
manual button press — the one-way git -> DB direction of the MVP.
"""

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Seed/refresh documentation pages from the bundled Markdown files."""
    try:
        count = env["tvbo.doc.page"].import_docs()
        _logger.info("tvbo_platform_docs post_init: imported %s page(s)", count)
    except Exception:  # pragma: no cover - never block install on a bad doc
        _logger.exception("tvbo_platform_docs post_init: documentation import failed")
