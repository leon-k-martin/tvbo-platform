# -*- coding: utf-8 -*-
{
    "name": "TVBO Platform Documentation",
    "version": "19.0.1.0.0",
    "category": "Research/Neuroscience",
    "summary": "Public how-to documentation (screencasts, screenshots, guides) for the TVBO platform.",
    "description": """
        tvbo_platform_docs serves the platform's user-facing documentation at
        /docs. The Markdown files under docs/ are the ground truth: a one-way
        git -> DB import (post-init hook + an "Import from git" backend button)
        turns them into tvbo.doc.page records that render to HTML and are served
        on the website in a 3-column docs shell (sidebar nav, content, on-this-
        page TOC) with server-side search.

        Pages embed the platform screencasts (MP4) and the e2e screenshots that
        ship under static/. Everything is public by default. The Markdown
        renderer is self-contained: it uses the optional `markdown` library when
        present, and otherwise falls back to a built-in renderer, so the module
        installs on an image that does not ship `markdown` (hence no
        external_dependencies declaration that would block install).
    """,
    "author": "Charité Universitätsmedizin Berlin",
    "website": "https://virtual-twin.github.io/tvbo/",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "security/ir.model.access.csv",
        "views/doc_page_views.xml",
        "views/doc_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "tvbo_platform_docs/static/src/css/docs.css",
            "tvbo_platform_docs/static/src/js/docs.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
    "auto_install": False,
}
