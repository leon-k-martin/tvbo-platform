# -*- coding: utf-8 -*-
"""Dereference TVB-O term IRIs: ``https://w3id.org/tvbo/<term>`` answers 303 with ``/ontology/<term>``.

The resolution itself lives in :mod:`..term_resolver`, which imports nothing from Odoo; this controller only reads the request and builds the response. ``cors='*'`` makes Odoo send ``Access-Control-Allow-Origin: *`` on every response of these routes and answer CORS preflights.
"""
from odoo import http
from odoo.http import request

from .. import term_resolver


class OntologyTerms(http.Controller):

    @http.route(["/ontology", "/ontology/"], type="http", auth="public", methods=["GET"], csrf=False, cors="*")
    def ontology(self, **kw):
        """Send the ontology root to its documentation."""
        return request.redirect(term_resolver.DOCS_URL, code=302, local=False)

    @http.route("/ontology/<path:term>", type="http", auth="public", methods=["GET"], csrf=False, cors="*")
    def term(self, term, **kw):
        """Describe one term as HTML or RDF, chosen by its path suffix or else the ``Accept`` header; 404 when the ontology says nothing about it."""
        name, media_type, negotiated = term_resolver.requested_format(term, request.httprequest.accept_mimetypes)
        headers = [("Vary", "Accept")] if negotiated else []
        iri = term_resolver.term_iri(name)
        description = term_resolver.describe(term_resolver.ontology_graph(), iri)
        if not description:
            body = f"Not a TVB-O term: {iri}\n"
            return request.make_response(body, headers + [("Content-Type", term_resolver.content_type("text/plain"))], status=404)
        if media_type == term_resolver.HTML:
            return request.render("tvbo.ontology_term", term_resolver.html_view(description, iri, name), headers=headers)
        body = term_resolver.serialise(description, media_type)
        return request.make_response(body, headers + [("Content-Type", term_resolver.content_type(media_type))])
