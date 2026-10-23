"""Plain-pytest tests of the TVB-O term resolver, ``odoo-addons/tvbo/term_resolver.py``, which imports nothing from Odoo.

Run with any Python that has rdflib, werkzeug and pytest, for instance the tvbo checkout's venv: ``<tvbo>/.venv/bin/python -m pytest tests/test_term_resolver.py``. The test against the packaged ontology also needs ``tvbo`` and skips without it.
"""
import importlib.util
from pathlib import Path

import pytest
from rdflib import RDF, Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDFS
from werkzeug.datastructures import MIMEAccept
from werkzeug.http import parse_accept_header

_SPEC = importlib.util.spec_from_file_location("term_resolver", Path(__file__).resolve().parents[1] / "odoo-addons" / "tvbo" / "term_resolver.py")
term_resolver = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(term_resolver)

BROWSER = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
CORNER = URIRef("https://w3id.org/tvbo/Corner#upper%20right")
FIXTURE = """
@prefix tvbo: <https://w3id.org/tvbo/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

tvbo:Dynamics a owl:Class ;
    rdfs:label "Dynamics" ;
    skos:definition "A system of <equations> & parameters." ;
    rdfs:seeAlso <https://example.org/dynamics> ;
    rdfs:subClassOf [ a owl:Restriction ; owl:onProperty tvbo:parameters ; owl:minCardinality "0"^^xsd:nonNegativeInteger ] .

<https://w3id.org/tvbo/JansenRit/state_variables/y0> a tvbo:StateVariable .

tvbo:Corner a owl:Class ; rdfs:label "Corner" .
<https://w3id.org/tvbo/Corner#upper%20right> a tvbo:Corner ; rdfs:label "upper right" .

tvbo:Unrelated a owl:Class ; rdfs:label "Unrelated" .
"""


@pytest.fixture(scope="module")
def graph():
    return Graph().parse(data=FIXTURE, format="turtle")


def accept(header):
    """Parse `header` the way werkzeug parses ``request.accept_mimetypes``."""
    return parse_accept_header(header, MIMEAccept)


@pytest.mark.parametrize(
    ("term", "name", "media_type"),
    [
        ("Dynamics.ttl", "Dynamics", "text/turtle"),
        ("models/JansenRit.ttl", "models/JansenRit", "text/turtle"),
        ("Dynamics.jsonld", "Dynamics", "application/ld+json"),
        ("Dynamics.rdf", "Dynamics", "application/rdf+xml"),
        ("software/NetworkDynamics.jl.nt", "software/NetworkDynamics.jl", "application/n-triples"),
    ],
)
def test_suffix_names_the_format_over_accept(term, name, media_type):
    assert term_resolver.requested_format(term, accept(BROWSER)) == (name, media_type, False)


@pytest.mark.parametrize("term", ["Dynamics", "software/NetworkDynamics.jl", "tvbo.owl", "study/age"])
def test_any_other_dot_belongs_to_the_name(term):
    assert term_resolver.requested_format(term, accept("text/turtle")) == (term, "text/turtle", True)


@pytest.mark.parametrize(
    ("header", "media_type"),
    [
        (BROWSER, "text/html"),
        ("*/*", "text/html"),
        (None, "text/html"),
        ("application/json", "text/html"),
        ("text/turtle", "text/turtle"),
        ("application/ld+json", "application/ld+json"),
        ("application/rdf+xml", "application/rdf+xml"),
        ("application/n-triples", "application/n-triples"),
        ("text/turtle;q=0.5, application/ld+json", "application/ld+json"),
    ],
)
def test_accept_negotiates_the_format(header, media_type):
    assert term_resolver.requested_format("Dynamics", accept(header)) == ("Dynamics", media_type, True)


def test_content_type_declares_utf8_on_text_types_only():
    assert term_resolver.content_type("text/turtle") == "text/turtle; charset=utf-8"
    assert term_resolver.content_type("application/ld+json") == "application/ld+json"


def test_description_is_the_cbd_including_blank_nodes(graph):
    iri = term_resolver.term_iri("Dynamics")
    description = term_resolver.describe(graph, iri)
    restriction = description.value(iri, RDFS.subClassOf)
    assert len(description) == 8
    assert (restriction, OWL.onProperty, term_resolver.term_iri("parameters")) in description
    assert (term_resolver.term_iri("Unrelated"), None, None) not in description


def test_description_covers_the_terms_under_its_fragments(graph):
    description = term_resolver.describe(graph, term_resolver.term_iri("Corner"))
    assert (CORNER, RDFS.label, Literal("upper right")) in description


@pytest.mark.parametrize("name", ["NoSuchTerm", "parameters"])
def test_a_term_that_is_no_subject_has_an_empty_description(graph, name):
    assert not term_resolver.describe(graph, term_resolver.term_iri(name))


@pytest.mark.parametrize("media_type", list(term_resolver.RDF_FORMATS))
def test_every_serialisation_parses_back_to_the_description(graph, media_type):
    description = term_resolver.describe(graph, term_resolver.term_iri("Dynamics"))
    text = term_resolver.serialise(description, media_type)
    assert isomorphic(Graph().parse(data=text, format=term_resolver.RDF_FORMATS[media_type].serializer), description)


def test_turtle_binds_the_tvbo_prefix(graph):
    description = term_resolver.describe(graph, term_resolver.term_iri("Dynamics"))
    assert "@prefix tvbo: <https://w3id.org/tvbo/> ." in term_resolver.serialise(description, "text/turtle")


def test_html_view_lists_label_types_definition_rows_and_serialisations(graph):
    iri = term_resolver.term_iri("Dynamics")
    view = term_resolver.html_view(term_resolver.describe(graph, iri), iri, "Dynamics")
    (block,) = view["blocks"]
    objects = {row["predicate"]["text"]: row["object"] for row in block["rows"]}
    restriction = {row["predicate"]["text"]: row["object"] for row in objects["rdfs:subClassOf"]["rows"]}
    assert (block["label"], block["iri"], block["anchor"]) == ("Dynamics", str(iri), None)
    assert block["types"] == [{"text": "owl:Class", "href": str(OWL.Class), "rows": None}]
    assert block["descriptions"] == ["A system of <equations> & parameters."]
    assert objects["rdfs:seeAlso"] == {"text": "https://example.org/dynamics", "href": "https://example.org/dynamics", "rows": None}
    assert restriction["owl:onProperty"] == {"text": "tvbo:parameters", "href": "https://w3id.org/tvbo/parameters", "rows": None}
    assert [link["href"] for link in view["serialisations"]] == [f"/ontology/Dynamics{suffix}" for suffix in (".ttl", ".jsonld", ".rdf", ".nt")]


def test_html_view_falls_back_to_the_local_name(graph):
    iri = term_resolver.term_iri("JansenRit/state_variables/y0")
    view = term_resolver.html_view(term_resolver.describe(graph, iri), iri, "JansenRit/state_variables/y0")
    assert view["blocks"][0]["label"] == "y0"
    assert view["serialisations"][0]["href"] == "/ontology/JansenRit/state_variables/y0.ttl"


def test_serialisation_links_quote_the_name(graph):
    name = "Corner#upper%20right"
    view = term_resolver.html_view(term_resolver.describe(graph, term_resolver.term_iri(name)), CORNER, name)
    assert view["serialisations"][0]["href"] == "/ontology/Corner%23upper%2520right.ttl"


def test_html_view_puts_the_term_first_and_anchors_its_fragments(graph):
    iri = term_resolver.term_iri("Corner")
    view = term_resolver.html_view(term_resolver.describe(graph, iri), iri, "Corner")
    assert [(block["iri"], block["anchor"]) for block in view["blocks"]] == [(str(iri), None), (str(CORNER), "upper%20right")]


def test_packaged_ontology_describes_dynamics():
    pytest.importorskip("tvbo")
    iri = term_resolver.term_iri("Dynamics")
    description = term_resolver.describe(term_resolver.ontology_graph(), iri)
    assert (iri, RDF.type, OWL.Class) in description
    assert term_resolver.ontology_graph() is term_resolver.ontology_graph()
