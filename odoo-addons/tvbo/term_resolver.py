# -*- coding: utf-8 -*-
"""Resolve TVB-O term IRIs to their descriptions, with no Odoo dependency.

``https://w3id.org/tvbo/<term>`` answers 303 with ``/ontology/<term>``, which :mod:`.controllers.ontology` serves from the functions here. A term's description is its Concise Bounded Description in the ontology shipped with the installed ``tvbo`` package, together with that of every ``<term>#<fragment>`` IRI, because a client strips the fragment before it dereferences a hash IRI such as ``MarkType#band``.
"""

import collections
import functools
import importlib.resources
import re
from typing import NamedTuple
from urllib.parse import quote, urldefrag

from rdflib import RDF, RDFS, BNode, Graph, URIRef
from rdflib.namespace import DCTERMS, SKOS

TERM_BASE = "https://w3id.org/tvbo/"
DOCS_URL = "https://virtual-twin.github.io/tvbo/ontology/"
HTML = "text/html"


class RdfFormat(NamedTuple):
    """An RDF serialisation of a term: its path suffix, rdflib serializer name and display title."""

    suffix: str
    serializer: str
    title: str


RDF_FORMATS = {
    "text/turtle": RdfFormat(".ttl", "turtle", "Turtle"),
    "application/ld+json": RdfFormat(".jsonld", "json-ld", "JSON-LD"),
    "application/rdf+xml": RdfFormat(".rdf", "xml", "RDF/XML"),
    "application/n-triples": RdfFormat(".nt", "nt", "N-Triples"),
}
MEDIA_TYPES = (HTML, *RDF_FORMATS)
LABELS = (RDFS.label, SKOS.prefLabel)
DESCRIPTIONS = (DCTERMS.description, SKOS.definition, RDFS.comment)


@functools.cache
def ontology_graph():
    """Return the ontology shipped in the installed ``tvbo`` package, parsed once per process."""
    source = importlib.resources.files("tvbo").joinpath("data", "ontology", "tvbo.owl")
    with importlib.resources.as_file(source) as path:
        return Graph().parse(path, format="xml")


def requested_format(term, accept):
    """Split a request path into the term name and the media type to answer in.

    A trailing ``.ttl``, ``.jsonld``, ``.rdf`` or ``.nt`` names the format and is not part of the name; any other dot, as in ``software/NetworkDynamics.jl``, belongs to the name. Without such a suffix the format is negotiated on `accept`, and HTML answers ``*/*`` or a request without ``Accept``.

    Args:
        term: The path after ``/ontology/``, as received.
        accept: The request's parsed ``Accept`` header, a werkzeug ``MIMEAccept``.

    Returns:
        ``(name, media_type, negotiated)``; `negotiated` is true when the answer depends on ``Accept``, so the response must vary on it.
    """
    for media_type, rdf_format in RDF_FORMATS.items():
        if term.endswith(rdf_format.suffix):
            return term.removesuffix(rdf_format.suffix), media_type, False
    return term, accept.best_match(MEDIA_TYPES, default=HTML), True


def term_iri(name):
    """Return the IRI of the term called `name`."""
    return URIRef(TERM_BASE + name)


def content_type(media_type):
    """Return the ``Content-Type`` value for `media_type`, declaring UTF-8 on text types."""
    return f"{media_type}; charset=utf-8" if media_type.startswith("text/") else media_type


def describe(graph, iri):
    """Return the CBD of `iri` in `graph` merged with the CBD of every ``<iri>#<fragment>`` subject.

    The result is empty when `graph` describes neither. It carries `graph`'s prefixes and binds ``tvbo`` to :data:`TERM_BASE`, so its Turtle reads in the ontology's own CURIEs.
    """
    description = Graph()
    for prefix, namespace in [*graph.namespaces(), ("tvbo", TERM_BASE)]:
        description.bind(prefix, namespace)
    for subject in [iri, *_fragment_terms(graph).get(str(iri), ())]:
        graph.cbd(subject, target_graph=description)
    return description


@functools.cache
def _fragment_terms(graph):
    """Map each IRI to the ``<IRI>#<fragment>`` subjects of `graph`, indexed once per graph because the served ontology never changes."""
    index = collections.defaultdict(list)
    for subject in set(graph.subjects()):
        if isinstance(subject, URIRef) and "#" in subject:
            index[subject.partition("#")[0]].append(subject)
    return index


def serialise(description, media_type):
    """Return `description` in the RDF serialisation that `media_type` names."""
    return description.serialize(format=RDF_FORMATS[media_type].serializer)


def html_view(description, iri, name):
    """Return the QWeb values of the page for the term `name`.

    ``blocks`` holds one entry per IRI the description is about, `iri` first, and ``serialisations`` links this term's four RDF forms under ``/ontology/``.
    """
    subjects = sorted({s for s in description.subjects() if isinstance(s, URIRef)}, key=lambda s: (s != iri, s))
    return {
        "blocks": [_block(description, subject) for subject in subjects],
        "serialisations": [
            {"media_type": media_type, "title": rdf_format.title, "href": "/ontology/" + quote(name + rdf_format.suffix)}
            for media_type, rdf_format in RDF_FORMATS.items()
        ],
    }


def _block(graph, subject):
    """Return the anchor, label, IRI, types, descriptions and predicate/object rows of `subject`."""
    return {
        "anchor": urldefrag(subject).fragment or None,
        "label": next((str(o) for p in LABELS for o in graph.objects(subject, p)), re.split("[/#]", subject)[-1]),
        "iri": str(subject),
        "types": [_node(graph, o) for o in graph.objects(subject, RDF.type)],
        "descriptions": [str(o) for p in DESCRIPTIONS for o in graph.objects(subject, p)],
        "rows": _rows(graph, subject),
    }


def _rows(graph, subject):
    """Return the predicate/object pairs of `subject` in `graph`, sorted by predicate."""
    return [{"predicate": _node(graph, p), "object": _node(graph, o)} for p, o in sorted(graph.predicate_objects(subject))]


def _node(graph, term):
    """Return how the page shows `term`: an IRI links to itself, a blank node nests its own rows, a literal is its text."""
    if isinstance(term, BNode):
        return {"text": "", "href": None, "rows": _rows(graph, term)}
    if isinstance(term, URIRef):
        return {"text": _curie(graph, term), "href": str(term), "rows": None}
    return {"text": str(term), "href": None, "rows": None}


def _curie(graph, iri):
    """Return `iri` as a CURIE under one of `graph`'s prefixes, or the IRI itself when no prefix covers it."""
    try:
        return graph.namespace_manager.curie(iri, generate=False)
    except (KeyError, ValueError):
        return str(iri)
