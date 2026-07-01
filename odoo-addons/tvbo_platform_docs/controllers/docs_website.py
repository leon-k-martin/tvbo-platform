# -*- coding: utf-8 -*-
"""Website controllers for the platform documentation.

The routes are ``auth="public"`` — anonymous visitors reach them. The platform
docs are public by default; :meth:`_visible_domain` keeps an ``access_level``
tier so a page can later be gated to staff/admin without a code change
(anonymous sees ``public`` only; internal users add ``internal``; system admins
see everything).
"""

import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TvboDocsController(http.Controller):

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------
    def _visible_domain(self):
        user = request.env.user
        if user.has_group("base.group_system"):
            return []
        if user.has_group("base.group_user"):
            return [("access_level", "in", ("internal", "public"))]
        return [("access_level", "=", "public")]

    def _page_or_none(self, slug):
        domain = [("slug", "=", slug)] + self._visible_domain()
        return request.env["tvbo.doc.page"].sudo().search(domain, limit=1)

    def _readable_pages(self):
        return request.env["tvbo.doc.page"].sudo().search(self._visible_domain())

    # ------------------------------------------------------------------
    # Navigation (sections are a single folder deep)
    # ------------------------------------------------------------------
    def _section_meta(self):
        """{category: (nav_label, nav_order)} from each folder's index.md.

        The root ``docs/index.md`` (no category) controls the category-less
        "general" bucket, so its nav_label/nav_order place the Getting Started
        page first rather than in a trailing "General" section.
        """
        meta = {}
        for idx in request.env["tvbo.doc.page"].sudo().search([("is_index", "=", True)]):
            meta[idx.category or "general"] = (idx.nav_label or "", idx.nav_order)
        return meta

    def _section_label(self, cat, meta):
        return (meta.get(cat) or ("", 0))[0] or (cat or "").replace("-", " ").title()

    def _section_order(self, cat, meta):
        """Sort key: the section's nav_order, then its name for stability."""
        return (meta.get(cat) or ("", 10 ** 6))[1], cat

    def _nav(self, pages, meta=None):
        """Sidebar sections -> [(label, index_slug, [sub_pages])], ordered.

        The section header is itself a link to that section's index page
        (``index_slug``), so the index is reached by clicking the heading rather
        than a redundant "Overview" entry. ``sub_pages`` therefore excludes the
        index page. A section with no index page yields ``index_slug = None``.
        """
        if meta is None:
            meta = self._section_meta()
        sections = {}
        for page in pages:
            sections.setdefault(page.category or "general", []).append(page)
        nav = []
        for cat in sorted(sections, key=lambda c: self._section_order(c, meta)):
            plist = sorted(sections[cat], key=lambda p: (p.sequence, p.name))
            index = next((p for p in plist if p.is_index), None)
            subs = [p for p in plist if not p.is_index]
            nav.append((self._section_label(cat, meta), index.slug if index else None, subs))
        return nav

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------
    @http.route("/docs", type="http", auth="public", website=True, sitemap=True)
    def docs_index(self, **kwargs):
        """/docs is an overview landing: one card per chapter (each section's
        index page), with a thumbnail and summary. The chapters themselves —
        Getting Started included — are reached from the cards, so the landing is
        a map of the guide rather than dropping straight into one page."""
        pages = self._readable_pages()
        chapters = sorted(
            (p for p in pages if p.is_index),
            key=lambda p: (p.nav_order, p.name),
        )
        return request.render(
            "tvbo_platform_docs.docs_index",
            {
                "nav": self._nav(pages),
                "active_slug": None,
                "chapters": chapters,
            },
        )

    @http.route("/docs/<string:slug>", type="http", auth="public", website=True, sitemap=True)
    def docs_page(self, slug, **kwargs):
        page = self._page_or_none(slug)
        if not page:
            if not request.env["tvbo.doc.page"].sudo().search_count([("slug", "=", slug)]):
                return request.redirect("/docs")
            if request.env.user._is_public():
                from urllib.parse import quote
                return request.redirect("/web/login?redirect=" + quote("/docs/%s" % slug, safe=""))
            return request.redirect("/docs")
        return self._render_page(page)

    def _render_page(self, page):
        """Render one page in the docs shell, with prev/next and breadcrumbs."""
        pages = self._readable_pages()
        meta = self._section_meta()
        ordered = sorted(
            pages,
            key=lambda p: (self._section_order(p.category or "general", meta), p.sequence, p.name),
        )
        idx = next((i for i, p in enumerate(ordered) if p.id == page.id), None)
        prev_page = ordered[idx - 1] if idx not in (None, 0) else None
        next_page = ordered[idx + 1] if idx is not None and idx + 1 < len(ordered) else None
        # Breadcrumb: section, then the page name for a non-index (sub) page. An
        # index page is the section itself, so it shows just the section.
        crumbs = [self._section_label(page.category or "general", meta)]
        if not page.is_index:
            crumbs.append(page.name)
        return request.render(
            "tvbo_platform_docs.docs_page",
            {
                "page": page,
                "nav": self._nav(pages, meta),
                "active_slug": page.slug,
                "prev_page": prev_page,
                "next_page": next_page,
                "crumbs": crumbs,
            },
        )

    @http.route("/docs/search", type="http", auth="public", website=False, sitemap=False, methods=["GET"])
    def docs_search(self, q=None, **kwargs):
        query = (q or "").strip()
        results = []
        if len(query) >= 2:
            meta = self._section_meta()
            domain = ["|", ("name", "ilike", query), ("content", "ilike", query)] + self._visible_domain()
            for page in request.env["tvbo.doc.page"].sudo().search(domain, limit=15):
                results.append({
                    "name": page.name,
                    "slug": page.slug,
                    "category": self._section_label(page.category or "general", meta),
                })
        return request.make_response(
            json.dumps(results),
            headers=[("Content-Type", "application/json; charset=utf-8")],
        )
