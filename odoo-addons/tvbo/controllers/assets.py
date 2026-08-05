# -*- coding: utf-8 -*-
"""Compressed delivery for this addon's static tree.

Odoo answers ``/<module>/static/<path>`` from :meth:`Request._serve_static`
before dispatch, so those files never reach the ``ir.http._post_dispatch`` hook
that compresses everything else (see :mod:`..compression`). ``/tvbo/z/<path>``
is the compressed door onto the same tree — templates link it instead of
``/tvbo/static/`` — and it caches each file's gzipped bytes against the mtime,
so there are no ``.gz`` artifacts to keep in sync with their sources.
"""

import gzip
import hashlib
import json
import mimetypes
import os

from werkzeug.exceptions import NotFound
from werkzeug.security import safe_join

from odoo import http
from odoo.http import request

from ..compression import LEVEL, OPAQUE, ByteLru, accepts_gzip

STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

CACHE_VERSIONED = "public, max-age=604800"
CACHE_PLAIN = "public, max-age=0, must-revalidate"

_files = ByteLru(48 * 1024 * 1024)


def _cache_control():
    """A week for `?v=`-busted links, revalidate-always for the rest.

    Most templates carry a cache-buster, but several links do not — the three.js
    bundle, the OBJ mesh, the portal and document-parser scripts — and a blanket
    week on those means an edit does not reach a returning browser until it
    expires. They still cost only a 304 each, because of the ETag below.
    """
    return CACHE_VERSIONED if request.httprequest.args.get("v") else CACHE_PLAIN


def json_payload(data, status=200, headers=()):
    """Serialise `data` as a JSON response; ``_post_dispatch`` gzips it.

    ``default=str`` so non-JSON-native values (date/datetime, Decimal) serialise
    as strings instead of raising and 500-ing the endpoint.
    """
    body = json.dumps(data, default=str).encode()
    out = list(headers) + [("Content-Type", "application/json"), ("Content-Length", str(len(body)))]
    response = request.make_response(body, out)
    response.status_code = status
    return response


def _load(path):
    """Return (etag, raw_or_None, gzipped_or_None), recompressing when it changes.

    Only one encoding is kept. Caching both would spend 26 MB of the budget on
    the 19.5 MB OBJ mesh alone and evict every stylesheet behind it; since every
    real client sends ``Accept-Encoding: gzip``, the raw bytes are held only for
    files that do not compress, and an identity request for the rest re-reads.
    """
    st = os.stat(path)
    stamp = (st.st_mtime_ns, st.st_size)
    hit = _files.get(path)
    if hit and hit[0] == stamp:
        return hit[1]
    with open(path, "rb") as fh:
        raw = fh.read()
    blob = None if os.path.splitext(path)[1].lower() in OPAQUE else gzip.compress(raw, LEVEL)
    if blob is not None and len(blob) >= len(raw):
        blob = None
    entry = ('W/"%s"' % hashlib.blake2b(raw, digest_size=12).hexdigest(), None if blob else raw, blob)
    _files.put(path, (stamp, entry), len(entry[1] or b"") + len(blob or b""))
    return entry


class TvboAssets(http.Controller):

    # auth="none": never touch request.env here, it is None
    @http.route("/tvbo/z/<path:path>", type="http", auth="none", methods=["GET"], csrf=False)
    def compressed(self, path, **kw):
        full = safe_join(STATIC, path)
        if not full or not os.path.isfile(full):
            raise NotFound()

        etag, raw, blob = _load(full)
        headers = [
            ("Content-Type", mimetypes.guess_type(path)[0] or "application/octet-stream"),
            ("Cache-Control", _cache_control()),
            ("ETag", etag),
            ("Vary", "Accept-Encoding"),
            ("X-Content-Type-Options", "nosniff"),
        ]
        if etag in (request.httprequest.headers.get("If-None-Match") or ""):
            response = request.make_response("", headers)
            response.status_code = 304
            return response

        gzipped = bool(blob) and accepts_gzip()
        if gzipped:
            body = blob
            headers.append(("Content-Encoding", "gzip"))
        elif raw is not None:
            body = raw
        else:  # compressible file, identity requested: the raw bytes are not cached
            with open(full, "rb") as fh:
                body = fh.read()
        headers.append(("Content-Length", str(len(body))))
        return request.make_response(body, headers)
