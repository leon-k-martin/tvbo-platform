# -*- coding: utf-8 -*-
"""Gzip on the way out — the only place this deployment compresses anything.

Odoo ships no HTTP compression of its own and the Kong ingress in ``k8s.yaml``
adds none, so responses used to leave raw: 3.9 MB of core asset bundles on every
page load, plus 20-88 KB of HTML per view that gzips to a fifth of that.

Two paths reach the wire, because :meth:`odoo.http.Request._serve_static` answers
``/<module>/static/<path>`` straight off disk *before* any dispatch happens:

* dispatched responses — HTML, ``/web/assets`` bundles, the JSON APIs — go
  through ``ir.http._post_dispatch`` into :func:`compress_response`
* addon static files go through the ``/tvbo/z/<path>`` controller in
  :mod:`.controllers.assets`, which keeps them compressed in a cache keyed on
  each file's mtime

Both share the primitives here so there is one gzip policy, not two.
"""

import gzip
import threading
from collections import OrderedDict

from odoo.http import request

LEVEL = 6

# below this, the gzip header costs more than the encoding saves
MIN_GZIP = 900

# compressing means buffering the whole body in memory; past this, let it stream
MAX_BODY = 12 * 1024 * 1024

# already-compressed payloads; gzip only burns CPU and adds bytes
OPAQUE = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff", ".woff2", ".gz", ".zip", ".mp4", ".webm"}

TEXTUAL = {
    "application/javascript",
    "text/javascript",
    "application/json",
    "application/ld+json",
    "application/manifest+json",
    "application/xml",
    "application/xhtml+xml",
    "application/wasm",
    "image/svg+xml",
}


class ByteLru:
    """LRU with a byte budget rather than an entry count.

    Every HTTP worker keeps its own copy of whatever it has compressed, so this
    has to be bounded by size, not by count: one entry here can be the 19.5 MB
    mesh in the static tree or a 3 MB asset bundle.

    Locked, because Odoo serves requests on threads and the running byte total is
    a read-modify-write: unsynchronised it drifts and the budget stops holding.
    """

    def __init__(self, budget):
        self.budget = budget
        self.bytes = 0
        self._items = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            self._items.move_to_end(key)
            return item[0]

    def put(self, key, value, size):
        with self._lock:
            old = self._items.pop(key, None)
            if old:
                self.bytes -= old[1]
            self._items[key] = (value, size)
            self.bytes += size
            while self.bytes > self.budget and len(self._items) > 1:
                self.bytes -= self._items.popitem(last=False)[1][1]
        return value


def accepts_gzip():
    return "gzip" in (request.httprequest.headers.get("Accept-Encoding") or "")


def compressible(content_type):
    """Is this media type worth gzipping?

    ``text/event-stream`` is excluded explicitly: buffering a bus stream to
    compress it would hold the response open forever.
    """
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype == "text/event-stream":
        return False
    return ctype.startswith("text/") or ctype in TEXTUAL


_bundles = ByteLru(32 * 1024 * 1024)


def _bundle_key(path, response):
    """Cache key for a ``/web/assets`` bundle, or None when it must not be cached.

    The hashed URL form is content-addressed, but ``/web/assets/debug/<file>`` and
    the ``any``/``%`` form are not — those paths stay constant while the bundle
    behind them changes, so keying on the path alone would pin a stale body until
    the worker restarts. The ETag tracks the content in every form, so key on it
    and skip caching entirely when there is none.
    """
    if not path.startswith("/web/assets/"):
        return None
    etag = response.headers.get("ETag")
    return "%s|%s" % (path, etag) if etag else None


def compress_response(response):
    """Gzip `response` in place when the client asked for it and it pays off.

    Mutates rather than returns, because ``ir.http._post_dispatch`` discards its
    return value and ``_serve_ir_http`` goes on to return the original object.
    """
    if response.status_code != 200 or response.headers.get("Content-Encoding"):
        return
    if not compressible(response.headers.get("Content-Type")) or not accepts_gzip():
        return
    if response.is_streamed and not response.direct_passthrough:
        return
    size = response.content_length
    if size is None and response.direct_passthrough:
        return  # a file stream of unknown length: buffering it is the bigger risk
    if (size or 0) > MAX_BODY:
        return

    key = _bundle_key(request.httprequest.full_path, response)
    cached = _bundles.get(key) if key else None
    if cached is None:
        if response.direct_passthrough:
            response.direct_passthrough = False
        body = response.get_data()
        if len(body) < MIN_GZIP:
            return
        blob = gzip.compress(body, LEVEL)
        if len(blob) >= len(body):
            return
        if key:
            _bundles.put(key, blob, len(blob))
    else:
        blob = cached
        response.direct_passthrough = False

    response.set_data(blob)
    response.headers["Content-Encoding"] = "gzip"
    # set the header by hand: Odoo's _Response lacks werkzeug's `vary` property
    vary = response.headers.get("Vary")
    if not vary:
        response.headers["Vary"] = "Accept-Encoding"
    elif "accept-encoding" not in vary.lower():
        response.headers["Vary"] = vary + ", Accept-Encoding"
    # a content coding weakens the entity-tag; If-None-Match still matches weakly
    etag = response.headers.get("ETag")
    if etag and not etag.startswith("W/"):
        response.headers["ETag"] = "W/" + etag
