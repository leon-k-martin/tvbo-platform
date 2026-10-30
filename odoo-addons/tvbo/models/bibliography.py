"""A study's bibliographic details, read by its citekey from the references.bib that ships with tvbo."""
import functools
import logging

_logger = logging.getLogger(__name__)

# Bib fields passed on as they are; a free-text abstract stays out (publishers hold its copyright), and so do reference-manager fields such as ``file``, a local path.
_PASSED_ON = ("volume", "number", "pages", "month", "publisher", "edition", "address", "isbn", "issn", "pmid", "url", "keywords", "note")


@functools.cache
def _entries():
    """The bib's entries by citekey, or none when the bib cannot be read."""
    try:
        from tvbo.data import db

        return db.load_bibliography().entries
    except Exception as exc:  # noqa: BLE001
        _logger.warning("references.bib unreadable, studies keep only their citekey: %s", exc)
        return {}


@functools.cache
def _text_backend():
    """pybtex's plain-text renderer, looked up once: ``render_as`` searches every installed package for it on each call."""
    from pybtex.plugin import find_plugin

    return find_plugin("pybtex.backends", "text")()


def _plain(latex):
    """*latex* as plain text, without the braces and accent commands BibTeX writes."""
    from pybtex.richtext import Text

    return Text.from_latex(latex).render(_text_backend())


@functools.cache
def study(citekey):
    """The bib's details of the study *citekey* names: the schema's title, authors (one per line, as the platform stores multi-valued text), year, doi and type, the venue (journal, book title or publisher) and the ``_PASSED_ON`` fields, which the schema leaves to the bib. Details the bib lacks are left out."""
    entry = _entries().get(citekey or "")
    if entry is None:
        return {}
    fields = entry.fields
    venue = fields.get("journal") or fields.get("booktitle") or fields.get("publisher")
    details = {
        "title": _plain(fields["title"]) if "title" in fields else None,
        "authors": "\n".join(_plain(str(person)) for person in entry.persons.get("author", [])),
        "year": int(fields["year"]) if fields.get("year", "").isdigit() else None,
        "doi": fields.get("doi"),
        "type": entry.type,
        "venue": _plain(venue) if venue else None,
        **{name: _plain(fields[name]) for name in _PASSED_ON if fields.get(name)},
    }
    return {name: value for name, value in details.items() if value}
