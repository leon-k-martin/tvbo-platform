# -*- coding: utf-8 -*-
"""tvbo.doc.page — a single Markdown documentation page.

MVP, one-way sync: the Markdown files under this module's ``docs/`` tree are
the ground truth. :meth:`import_docs` reads them into ``tvbo.doc.page`` records
(on install via the post-init hook, and on demand via the "Import from git"
button). Backend/website edits are *not* exported back to git — a re-import
overwrites them.

Rendering is self-contained: it uses the optional ``markdown`` library when it
is installed, and otherwise falls back to a small built-in renderer. This means
the module installs even on an Odoo image that does not ship ``markdown`` (so
the manifest deliberately declares no ``external_dependencies``). Relative image
and video sources resolve to this module's ``static/`` folder, and an ``<img>``
whose source is a video file (``.mp4``/``.webm``/…) is turned into a
``<video controls>`` so screencasts can be embedded with plain ``![](…)`` syntax.
"""

import logging
import os
import posixpath
import re

from odoo import _, api, fields, models
from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)

_MODULE = "tvbo_platform_docs"
_STATIC_PREFIX = "/%s/static" % _MODULE

# Optional rich pipeline (only when the `markdown` lib is present). Mirrors a
# MkDocs-ish feature set; falls back to the stdlib set, then to the built-in.
_MD_RICH_EXTENSIONS = ["tables", "fenced_code", "attr_list", "toc", "sane_lists", "admonition"]

# Relative <img|source src="..."> (not absolute, external, or data:).
_REL_SRC_RE = re.compile(r'(\bsrc=")(?!https?://|/|data:|#)([^"]+)(")', re.IGNORECASE)
# An <img> whose source is a video file -> rewrite to a <video> element.
_IMG_VIDEO_RE = re.compile(
    r'<img\b[^>]*?\bsrc="([^"]+\.(?:mp4|webm|mov|ogg|m4v))"[^>]*?>', re.IGNORECASE
)
# Every <a href="..."> so MkDocs-style *.md links resolve to /docs/<slug>.
_A_HREF_RE = re.compile(r'(<a\b[^>]*?\bhref=")([^"]+)(")', re.IGNORECASE)


def _slugify(value):
    """Lower-case, hyphenated, URL-safe slug (no http_routing dependency)."""
    value = (value or "").strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return value.strip("-") or "page"


def _escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class TvboDocPage(models.Model):
    _name = "tvbo.doc.page"
    _description = "TVBO Platform Documentation Page"
    _order = "category, sequence, name"

    name = fields.Char(string="Title", required=True)
    slug = fields.Char(
        string="Slug", required=True, copy=False, index=True,
        help="URL path segment, e.g. /docs/<slug>.",
    )
    category = fields.Char(
        string="Category", index=True,
        help="The section's folder path under docs/ (e.g. 'knowledge-graph').",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    is_index = fields.Boolean(
        help="True for a folder's index.md — the page that owns the section's nav metadata.",
    )
    nav_label = fields.Char(
        help="Sidebar header for this section (from the index page's `nav_label` front-matter).",
    )
    nav_order = fields.Integer(
        default=100,
        help="Ordering of this section in the sidebar (lower = earlier), from the "
        "index page's `nav_order` front-matter.",
    )
    summary = fields.Char(
        help="One-line description shown on the /docs overview cards "
        "(from the page's `summary` front-matter).",
    )
    thumbnail = fields.Char(
        help="Overview-card image path under this module's static/ folder, e.g. "
        "`img/kg-list-view.png` (from the page's `thumbnail` front-matter).",
    )

    content = fields.Text(
        string="Markdown",
        help="Markdown source. Ground truth lives in the git files under "
        "tvbo_platform_docs/docs/; a re-import overwrites edits made here.",
    )
    content_html = fields.Html(
        string="Rendered", compute="_compute_content_html", store=True,
        sanitize=False, sanitize_attributes=False,
        help="Rendered HTML, recomputed whenever the Markdown changes.",
    )

    access_level = fields.Selection(
        [("public", "Public"), ("internal", "Internal (staff only)"),
         ("system", "Admin only")],
        string="Visibility", default="public", required=True,
        help="Who may read this page. Platform docs are public by default.",
    )

    source_path = fields.Char(
        string="Source File", readonly=True, copy=False, index=True,
        help="Path of the originating Markdown file relative to the module root.",
    )
    last_import = fields.Datetime(string="Last Imported", readonly=True, copy=False)

    _sql_constraints = [
        ("slug_uniq", "unique(slug)", "The documentation slug must be unique."),
    ]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    @api.depends("content", "slug", "source_path")
    def _compute_content_html(self):
        for page in self:
            page.content_html = page._render_markdown(page.content or "")

    def _render_markdown(self, text):
        """Markdown -> HTML, with static assets, video embeds, and links fixed."""
        self.ensure_one()
        if not text:
            return False
        text = self._substitute_placeholders(text)
        html = self._markdown_to_html(text)
        html = self._rewrite_asset_urls(html)
        html = self._embed_videos(html)
        return self._rewrite_links(html)

    def _substitute_placeholders(self, text):
        """``{{base_url}}`` -> the configured web.base.url (no trailing slash)."""
        base = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        ).rstrip("/")
        return (text or "").replace("{{base_url}}", base)

    def _markdown_to_html(self, text):
        """Use the `markdown` lib if available, else the built-in renderer."""
        self.ensure_one()
        try:
            import markdown  # noqa: PLC0415
            return markdown.markdown(
                text, extensions=_MD_RICH_EXTENSIONS,
                extension_configs={"toc": {"permalink": False}},
            )
        except Exception:  # markdown lib absent or failed — use the built-in.
            return self._builtin_render(text)

    # ---- built-in (dependency-free) Markdown renderer ----------------
    def _builtin_render(self, text):
        """Render the subset of Markdown the platform docs use.

        Handles ATX headings (with anchor ids for the TOC), fenced code, GitHub
        pipe tables, ``!!! note`` admonitions, blockquotes, ordered/unordered
        lists, horizontal rules, raw-HTML blocks (e.g. <video>), and paragraphs.
        """
        lines = (text or "").replace("\r\n", "\n").split("\n")
        out, i, n = [], 0, len(lines)

        def is_block_start(s):
            return bool(
                re.match(r"(#{1,6})\s", s) or s.startswith(("```", ">", "!!! "))
                or re.match(r"\s*([-*+]|\d+\.)\s", s)
                or re.match(r"(\*{3,}|-{3,}|_{3,})\s*$", s)
                or s.lstrip().startswith("<")
            )

        while i < n:
            line = lines[i]

            # Fenced code block.
            if line.startswith("```"):
                lang = line[3:].strip()
                buf, i = [], i + 1
                while i < n and not lines[i].startswith("```"):
                    buf.append(lines[i]); i += 1
                i += 1
                cls = ' class="language-%s"' % lang if lang else ""
                out.append("<pre><code%s>%s</code></pre>" % (cls, _escape("\n".join(buf))))
                continue

            # Blank line.
            if not line.strip():
                i += 1; continue

            # Heading.
            m = re.match(r"(#{1,6})\s+(.*)", line)
            if m:
                level, txt = len(m.group(1)), m.group(2).strip()
                hid = _slugify(re.sub(r"[*`\[\]()]", "", txt))
                out.append("<h%d id=\"%s\">%s</h%d>" % (level, hid, self._inline(txt), level))
                i += 1; continue

            # Horizontal rule.
            if re.match(r"(\*{3,}|-{3,}|_{3,})\s*$", line):
                out.append("<hr/>"); i += 1; continue

            # Admonition: !!! type "Optional title" + indented body.
            m = re.match(r'!!!\s+(\w+)(?:\s+"([^"]*)")?\s*$', line)
            if m:
                kind = m.group(1).lower()
                title = m.group(2) if m.group(2) is not None else kind.title()
                buf, i = [], i + 1
                while i < n and (lines[i].startswith(("    ", "\t")) or not lines[i].strip()):
                    buf.append(re.sub(r"^(\t|    )", "", lines[i])); i += 1
                out.append(
                    '<div class="o_docs_admonition o_docs_admonition_%s">'
                    '<p class="o_docs_admonition_title">%s</p>%s</div>'
                    % (kind, _escape(title), self._builtin_render("\n".join(buf)))
                )
                continue

            # Blockquote.
            if line.startswith(">"):
                buf = []
                while i < n and lines[i].startswith(">"):
                    buf.append(lines[i][1:].lstrip()); i += 1
                out.append("<blockquote>%s</blockquote>" % self._builtin_render("\n".join(buf)))
                continue

            # GitHub pipe table (header row + |---|--- separator).
            if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
                out.append(self._render_table(lines, i, n))
                # advance past the table
                i += 2
                while i < n and "|" in lines[i] and lines[i].strip():
                    i += 1
                continue

            # List (unordered or ordered), allowing simple nested indentation.
            if re.match(r"\s*([-*+]|\d+\.)\s+", line):
                block, i = [], i
                while i < n and (re.match(r"\s*([-*+]|\d+\.)\s+", lines[i]) or
                                 (lines[i].startswith(("    ", "\t")) and lines[i].strip())):
                    block.append(lines[i]); i += 1
                out.append(self._render_list(block))
                continue

            # Raw HTML block (e.g. an embedded <video> …): pass through verbatim
            # until a blank line.
            if line.lstrip().startswith("<"):
                buf = []
                while i < n and lines[i].strip():
                    buf.append(lines[i]); i += 1
                out.append("\n".join(buf))
                continue

            # Paragraph: gather consecutive non-block lines.
            buf = []
            while i < n and lines[i].strip() and not is_block_start(lines[i]):
                buf.append(lines[i].strip()); i += 1
            out.append("<p>%s</p>" % self._inline(" ".join(buf)))

        return "\n".join(out)

    def _render_table(self, lines, start, n):
        def cells(row):
            row = row.strip().strip("|")
            return [c.strip() for c in row.split("|")]

        header = cells(lines[start])
        body = []
        j = start + 2
        while j < n and "|" in lines[j] and lines[j].strip():
            body.append(cells(lines[j])); j += 1
        html = ['<table class="table o_docs_table"><thead><tr>']
        html += ["<th>%s</th>" % self._inline(h) for h in header]
        html.append("</tr></thead><tbody>")
        for r in body:
            html.append("<tr>" + "".join("<td>%s</td>" % self._inline(c) for c in r) + "</tr>")
        html.append("</tbody></table>")
        return "".join(html)

    def _render_list(self, block):
        """Render a (possibly one-level-nested) list block to <ul>/<ol>."""
        ordered = bool(re.match(r"\s*\d+\.\s", block[0]))
        tag = "ol" if ordered else "ul"
        items, cur, cur_sub = [], None, []
        for ln in block:
            m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)", ln)
            if m and len(m.group(1)) < 2:  # top-level item
                if cur is not None:
                    items.append((cur, cur_sub)); cur_sub = []
                cur = m.group(3)
            elif m:  # nested item (>=2 spaces indent)
                cur_sub.append(m.group(3))
            elif cur is not None:  # continuation line
                cur = cur + " " + ln.strip()
        if cur is not None:
            items.append((cur, cur_sub))
        html = ["<%s>" % tag]
        for text, subs in items:
            li = "<li>%s" % self._inline(text)
            if subs:
                li += "<ul>" + "".join("<li>%s</li>" % self._inline(s) for s in subs) + "</ul>"
            li += "</li>"
            html.append(li)
        html.append("</%s>" % tag)
        return "".join(html)

    def _inline(self, s):
        """Inline Markdown: code spans (protected) then images, links, emphasis.

        Code spans are stashed out first so emphasis markers (``**`` ``__`` ``*``)
        inside backticks stay literal, e.g. ``__init__`` renders verbatim.
        """
        s = _escape(s)
        spans = []

        def _stash(match):
            spans.append(match.group(1))  # already escaped
            return "\x00%d\x00" % (len(spans) - 1)

        s = re.sub(r"`([^`]+)`", _stash, s)
        s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img alt="\1" src="\2"/>', s)
        s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\*\w])\*(?!\*)([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
        return re.sub(r"\x00(\d+)\x00", lambda m: "<code>%s</code>" % spans[int(m.group(1))], s)

    # ---- post-render fixups ------------------------------------------
    def _rewrite_asset_urls(self, html):
        """Resolve relative <img|source src="img/…|video/…"> to the module static."""
        def repl(match):
            return "%s%s/%s%s" % (match.group(1), _STATIC_PREFIX, match.group(2), match.group(3))
        return _REL_SRC_RE.sub(repl, html)

    def _embed_videos(self, html):
        """Turn an <img> that points at a video file into a <video controls>."""
        def repl(match):
            src = match.group(1)
            return (
                '<video class="o_docs_video" controls preload="metadata">'
                '<source src="%s"/>'
                'Your browser cannot play this video — '
                '<a href="%s">download it</a>.</video>' % (src, src)
            )
        return _IMG_VIDEO_RE.sub(repl, html)

    def _rewrite_links(self, html):
        """Resolve MkDocs-style relative *.md links to /docs/<slug> URLs."""
        self.ensure_one()
        cur_rel = re.sub(r"^docs[/\\]+", "", (self.source_path or "").replace("\\", "/"))
        cur_dir = posixpath.dirname(cur_rel)

        def repl(match):
            pre, href, post = match.group(1), match.group(2), match.group(3)
            low = href.lower()
            if low.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#", "/")):
                return match.group(0)
            path_part, _sep, anchor = href.partition("#")
            if path_part.endswith(".md"):
                target = posixpath.normpath(posixpath.join(cur_dir, path_part) if cur_dir else path_part)
                slug = self._slug_parts(os.path.splitext(target)[0])
                url = "/docs/%s" % slug
                if anchor:
                    url += "#" + anchor
                return "%s%s%s" % (pre, url, post)
            return match.group(0)

        return _A_HREF_RE.sub(repl, html)

    # ------------------------------------------------------------------
    # git -> DB import (one-way, MVP)
    # ------------------------------------------------------------------
    @api.model
    def _docs_root(self):
        module_path = get_module_path(_MODULE)
        if not module_path:
            return None
        root = os.path.join(module_path, "docs")
        return root if os.path.isdir(root) else None

    @api.model
    def _title_from_markdown(self, text, fallback):
        for line in (text or "").splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return fallback

    @api.model
    def _split_front_matter(self, text):
        """Split optional leading YAML front-matter -> (meta_dict, body)."""
        if not text or not text.startswith("---"):
            return {}, text or ""
        match = re.match(r"^---[ \t]*\r?\n(.*?\r?\n)---[ \t]*\r?\n?", text, re.DOTALL)
        if not match:
            return {}, text
        meta = {}
        for line in match.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _sep, val = line.partition(":")
            meta[key.strip().lower()] = val.strip().strip('"').strip("'")
        return meta, text[match.end():]

    @api.model
    def _slug_from_relpath(self, abs_path, root):
        rel_no_ext = os.path.splitext(os.path.relpath(abs_path, root))[0]
        return self._slug_parts(rel_no_ext.replace(os.sep, "/"))

    @api.model
    def _slug_parts(self, rel_no_ext):
        """Slug from a '/'-joined doc path (no extension). Drops trailing 'index'."""
        parts = [p for p in rel_no_ext.split("/") if p not in ("", ".")]
        if parts and parts[-1] == "index":
            parts = parts[:-1]
        return _slugify("-".join(parts) or "home")

    @api.model
    def import_docs(self):
        """Walk docs/**/*.md and upsert one tvbo.doc.page per file (idempotent)."""
        root = self._docs_root()
        if not root:
            _logger.warning("tvbo_platform_docs: no docs/ directory found; nothing to import")
            return 0

        module_path = get_module_path(_MODULE)
        now = fields.Datetime.now()
        touched = 0

        for dirpath, _dirs, files in os.walk(root):
            for filename in sorted(files):
                if not filename.lower().endswith(".md"):
                    continue
                abs_path = os.path.join(dirpath, filename)
                source_path = os.path.relpath(abs_path, module_path)
                try:
                    with open(abs_path, encoding="utf-8") as handle:
                        text = handle.read()
                except OSError:
                    _logger.warning("tvbo_platform_docs: cannot read %s", abs_path, exc_info=True)
                    continue

                base = os.path.splitext(filename)[0]
                rel_dir = os.path.relpath(dirpath, root)
                category = False if rel_dir == "." else rel_dir.replace(os.sep, "/")

                meta, body = self._split_front_matter(text)
                vals = {
                    "name": (meta.get("title") or "").strip() or self._title_from_markdown(body, base),
                    "content": body,
                    "category": category,
                    "is_index": base == "index",
                    "last_import": now,
                    "nav_label": meta.get("nav_label") or False,
                    "summary": meta.get("summary") or False,
                    "thumbnail": meta.get("thumbnail") or False,
                }
                for key in ("sequence", "nav_order"):
                    if meta.get(key):
                        try:
                            vals[key] = int(meta[key])
                        except (TypeError, ValueError):
                            pass
                access = (meta.get("access_level") or "").strip().lower()
                if access in ("public", "internal", "system"):
                    vals["access_level"] = access

                existing = self.with_context(active_test=False).search(
                    [("source_path", "=", source_path)], limit=1
                )
                if existing:
                    existing.write(vals)
                else:
                    vals["source_path"] = source_path
                    vals["slug"] = self._unique_slug(self._slug_from_relpath(abs_path, root))
                    vals.setdefault("access_level", "public")
                    self.create(vals)
                touched += 1

        _logger.info("tvbo_platform_docs: imported %s documentation page(s)", touched)
        return touched

    @api.model
    def _unique_slug(self, base):
        candidate, index = base, 2
        while self.with_context(active_test=False).search_count([("slug", "=", candidate)]):
            candidate = "%s-%s" % (base, index)
            index += 1
        return candidate

    def action_open_website(self):
        """Open this page on the public docs site."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": "/docs/%s" % (self.slug or ""),
            "target": "new",
        }

    def action_import_docs(self):
        """Backend button: re-import the git docs and report the count."""
        count = self.import_docs()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Documentation imported"),
                "message": _("%s page(s) synced from git.") % count,
                "type": "success",
                "sticky": False,
            },
        }
