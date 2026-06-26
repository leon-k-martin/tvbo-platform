# -*- coding: utf-8 -*-
"""
Knowledge Graph API - Clean MVP implementation.
No fallbacks. Fails fast when something unexpected happens.
"""
import json
import logging
import os
import re

from odoo import http
from odoo.http import Response, request

_logger = logging.getLogger(__name__)

# Singleton ontology API
_ontology_api = None

# Thumbnail directory (static files in the addon)
_THUMB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'src', 'img', 'thumbnails')
_THUMB_URL = '/tvbo/static/src/img/thumbnails'

# Report directory (pre-rendered markdown)
_REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'src', 'reports')
_REPORT_URL = '/tvbo/static/src/reports'

_KG_ENTITY_CONFIG = {
    'dynamics': {
        'model': 'tvbo.dynamics',
        'thumbnail': 'models',
        'report': 'models',
    },
    'network': {
        'model': 'tvbo.network',
        'thumbnail': 'networks',
        'report': 'networks',
    },
    'integrator': {
        'model': 'tvbo.integrator',
        'thumbnail': 'integrators',
        'report': 'integrators',
    },
    'experiment': {
        'model': 'tvbo.simulation_experiment',
        'thumbnail': 'experiments',
        'report': 'experiments',
    },
    # The ingested bibliographic studies live in tvbo.study (rec_name=title);
    # tvbo.simulation_study is a distinct, currently-empty experiment-container
    # concept, so pointing the KG 'study' card there showed 0 results.
    'study': {
        'model': 'tvbo.study',
        'thumbnail': 'studies',
        'report': 'studies',
    },
    'graph_generator': {
        'model': 'tvbo.graph_generator',
        'thumbnail': 'graph_generators',
        'report': 'graph_generators',
    },
    'continuation': {
        'model': 'tvbo.continuation',
        'thumbnail': 'continuations',
        'report': 'continuations',
    },
    'coupling': {
        'model': 'tvbo.coupling',
        'thumbnail': 'coupling_functions',
        'report': 'coupling_functions',
    },
    'observation': {
        'model': 'tvbo.observation',
        'thumbnail': 'observation_models',
        'report': 'observation_models',
    },
    'atlas': {
        'model': 'tvbo.brain_atlas',
        'thumbnail': 'atlases',
        'report': 'atlases',
    },
    # The software/ ground truth (neurolib, Brian2, Arbor, …) are SimulationTool
    # records in tvbo.simulation_tool — NOT tvbo.software_requirement, which is the
    # narrower per-dependency concept and had only nested records.
    'software': {
        'model': 'tvbo.simulation_tool',
        'thumbnail': 'software',
        'report': 'software',
    },
}

_KG_INTERNAL_FIELDS = {
    'id',
    'display_name',
    'create_uid',
    'create_date',
    'write_uid',
    'write_date',
    '__last_update',
    'linkml_meta',
}

_KG_LIST_FIELD_TYPES = {
    'char',
    'text',
    'html',
    'integer',
    'float',
    'monetary',
    'boolean',
    'selection',
    'date',
    'datetime',
}

_KG_DETAIL_FIELD_TYPES = _KG_LIST_FIELD_TYPES | {'one2many', 'many2many'}


def _get_model_or_none(model_name):
    """Return sudo model proxy or None if the model is unavailable."""
    try:
        return request.env[model_name].sudo()
    except Exception as e:
        _logger.warning('KG model unavailable: %s (%s)', model_name, e)
        return None


def _iter_available_entity_configs():
    """Yield (entity_type, cfg, model) for registered and available KG entities."""
    for entity_type, cfg in _KG_ENTITY_CONFIG.items():
        model = _get_model_or_none(cfg['model'])
        if model is None:
            continue
        yield entity_type, cfg, model


def _safe_asset_name(name: str) -> str:
    """Sanitize a name for filesystem lookup (replace colons, slashes, etc.)."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _thumbnail_url(category: str, name: str) -> str | None:
    """Return the URL for a thumbnail if it exists on disk."""
    safe = _safe_asset_name(name)
    png = os.path.join(_THUMB_DIR, category, f'{safe}.png')
    if os.path.isfile(png):
        from urllib.parse import quote
        return f'{_THUMB_URL}/{category}/{quote(safe)}.png'
    return None


def _report_url(category: str, name: str) -> str | None:
    """Return the URL for a pre-rendered report if it exists on disk."""
    safe = _safe_asset_name(name)
    md = os.path.join(_REPORT_DIR, category, f'{safe}.md')
    if os.path.isfile(md):
        from urllib.parse import quote
        return f'{_REPORT_URL}/{category}/{quote(safe)}.md'
    return None


def _extract_equation_latex(category: str, name: str) -> str | None:
    """Extract the first LaTeX equation from a report markdown file."""
    safe = _safe_asset_name(name)
    md_path = os.path.join(_REPORT_DIR, category, f'{safe}.md')
    if not os.path.isfile(md_path):
        return None
    with open(md_path, 'r') as f:
        content = f.read()
    match = re.search(r'\$\$(.+?)\$\$', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def get_ontology_api():
    """Get DirectOntologyAPI singleton. Fails if unavailable."""
    global _ontology_api
    if _ontology_api is None:
        from tvbo.api.direct_ontology_api import get_direct_ontology_api
        _ontology_api = get_direct_ontology_api()
    return _ontology_api


def json_response(data, status=200):
    """Standard JSON response with CORS. ``default=str`` so non-JSON-native values
    (date/datetime — e.g. SimulationTool.date_created — Decimal, etc.) serialize as
    strings instead of raising and 500-ing the whole endpoint."""
    return Response(
        json.dumps(data, default=str),
        content_type='application/json',
        status=status,
        headers={'Access-Control-Allow-Origin': '*'}
    )


def _safe_search_read(model_name, fields, domain=None, limit=None):
    """Read only compatible fields and retry on stale DB columns.

    This keeps KG endpoints working when Python models and DB schema are temporarily out of sync.
    """
    model = request.env[model_name].sudo()
    requested_fields = [f for f in fields if f in model._fields]
    if 'id' not in requested_fields:
        requested_fields.insert(0, 'id')

    while True:
        try:
            return model.search_read(domain or [], requested_fields, limit=limit)
        except Exception as e:
            msg = str(e)

            # Odoo field mismatch, e.g. "Invalid field 'foo' on 'tvbo.bar'"
            invalid_field_match = re.search(r"Invalid field '([^']+)'", msg)
            if invalid_field_match:
                bad_field = invalid_field_match.group(1)
                if bad_field in requested_fields:
                    requested_fields.remove(bad_field)
                    request.env.cr.rollback()
                    continue

            # PostgreSQL schema mismatch, e.g. "column tvbo_x.y does not exist"
            missing_col_match = re.search(r'column\s+(?:[\w\"]+\.)?([\w_]+)\s+does not exist', msg)
            if missing_col_match:
                missing_col = missing_col_match.group(1).strip('"')

                # Most fields map directly to a same-name SQL column
                if missing_col in requested_fields and missing_col != 'id':
                    requested_fields.remove(missing_col)
                    request.env.cr.rollback()
                    continue

                # Fallback: try matching by field.column
                removed = False
                for fname in list(requested_fields):
                    if fname == 'id':
                        continue
                    field = model._fields.get(fname)
                    if getattr(field, 'column', None) == missing_col:
                        requested_fields.remove(fname)
                        removed = True
                if removed:
                    request.env.cr.rollback()
                    continue

            raise


def _get_model_field_names(model_name, include_relations=False):
    """Get serializable field names from model metadata.

    This is schema-driven and adapts automatically to generated model changes.
    """
    model = request.env[model_name].sudo()
    allowed_types = _KG_DETAIL_FIELD_TYPES if include_relations else _KG_LIST_FIELD_TYPES

    field_names = []
    for field_name, field in model._fields.items():
        if field_name in _KG_INTERNAL_FIELDS:
            continue
        if field.type not in allowed_types:
            continue

        # Skip non-stored scalar fields to avoid triggering heavy compute paths.
        if field.type in _KG_LIST_FIELD_TYPES and not getattr(field, 'store', True):
            continue

        field_names.append(field_name)

    return sorted(field_names)


def _normalize_field_value(field, value, detail=False):
    """Normalize ORM values to JSON-safe primitives."""
    if value is None:
        return None

    # Keep explicit boolean false values
    if value is False and field.type != 'boolean':
        return None

    if field.type == 'many2one':
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            rec_id, rec_label = value[0], value[1]
            if detail:
                return {'id': rec_id, 'label': rec_label}
            return rec_label or rec_id
        return value

    if field.type in ('one2many', 'many2many'):
        return value if detail else None

    return value


def _normalize_row(model_name, row, detail=False):
    """Normalize a search_read row using model field metadata."""
    model = request.env[model_name].sudo()
    normalized = {}

    for field_name, value in row.items():
        if field_name == 'id':
            normalized['id'] = value
            continue

        field = model._fields.get(field_name)
        if not field:
            continue

        normalized_value = _normalize_field_value(field, value, detail=detail)
        if normalized_value is None:
            continue
        if normalized_value == '':
            continue
        if normalized_value == []:
            continue
        if normalized_value == {}:
            continue

        normalized[field_name] = normalized_value

    if 'id' not in normalized and row.get('id') is not None:
        normalized['id'] = row['id']

    return normalized


def _get_display_name(data, entity_type):
    """Get a stable display name from common schema fields."""
    for key in ('name', 'label', 'title', 'method', 'key'):
        value = data.get(key)
        if value:
            return str(value)

    rec_id = data.get('id')
    if rec_id is not None:
        return f'{entity_type.capitalize()} {rec_id}'

    return entity_type.capitalize()


def _odoo_field_to_property_schema(field_name, field):
    """Convert an Odoo field definition to KG property schema."""
    if field.type in ('char', 'text', 'html', 'date', 'datetime', 'many2one'):
        return {
            'type': 'string',
            'label': field.string or _field_label(field_name),
            'description': field.help or '',
        }

    if field.type in ('integer', 'float', 'monetary'):
        return {
            'type': 'number',
            'label': field.string or _field_label(field_name),
            'description': field.help or '',
        }

    if field.type == 'boolean':
        return {
            'type': 'boolean',
            'label': field.string or _field_label(field_name),
            'description': field.help or '',
        }

    if field.type == 'selection':
        values = []
        if isinstance(field.selection, (list, tuple)):
            for item in field.selection:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    values.append({'value': item[0], 'label': item[1]})

        return {
            'type': 'enum',
            'label': field.string or _field_label(field_name),
            'description': field.help or '',
            'values': values,
        }

    return None


def _field_label(field_name):
    """Convert field_name to a human-readable label."""
    return field_name.replace('_', ' ').title()


class KnowledgeGraphAPI(http.Controller):
    """Knowledge Graph API endpoints. Clean MVP."""

    # ===================
    # Schema
    # ===================

    @http.route('/tvbo/api/kg/schema', type='http', auth='public', methods=['GET'], csrf=False)
    def get_schema(self, **kw):
        """Get browser schema configuration."""
        searchable_fields = {'name', 'label', 'title', 'description'}

        for _, cfg, model in _iter_available_entity_configs():
            model_name = cfg['model']
            for field_name in _get_model_field_names(model_name, include_relations=False):
                field = model._fields.get(field_name)
                if not field:
                    continue
                if field.type in ('char', 'text', 'html', 'selection'):
                    searchable_fields.add(field_name)

        return json_response({
            "searchableFields": sorted(searchable_fields),
            "facets": [
                {"field": "type", "label": "Class", "type": "string"},
            ],
            "sources": ["database", "ontology"]
        })

    @http.route('/tvbo/api/kg/schema/classes', type='http', auth='public', methods=['GET'], csrf=False)
    def get_class_schemas(self, **kw):
        """Get schemas for all datamodel classes represented in the KG.

        Introspects Odoo models (generated from schema/tvbo_datamodel.yaml) to return
        class names, descriptions, and filterable properties with types.
        """
        result = {}
        for type_key, cfg, model in _iter_available_entity_configs():
            model_name = cfg['model']
            properties = {}
            for field_name, field in model._fields.items():
                if field_name in _KG_INTERNAL_FIELDS:
                    continue
                prop = _odoo_field_to_property_schema(field_name, field)
                if prop:
                    properties[field_name] = prop

            result[type_key] = {
                'class_name': model_name,
                'label': model._description or model_name,
                'description': model._description or '',
                'properties': properties,
            }

        return json_response(result)

    # ===================
    # Health / deploy diagnostics
    # ===================

    @http.route('/tvbo/api/kg/health', type='http', auth='public', methods=['GET'], csrf=False)
    def get_health(self, **kw):
        """KG health check — the diagnostic surface reachable without kubectl.

        Returns per-entity database row counts and an overall verdict so the
        deploy outcome is visible over HTTP. ``kg_ok`` is false when the
        building-block tables are empty (the public KG would then show only the
        ontology), which means the deploy's ``seed_database`` step did not run.
        """
        counts = {}
        for entity_type, cfg, model in _iter_available_entity_configs():
            try:
                counts[entity_type] = model.search_count([])
            except Exception as e:  # noqa: BLE001
                counts[entity_type] = 'error: %s' % e

        ontology_count = None
        try:
            ontology_count = len(self._get_ontology_concepts(''))
        except Exception:  # noqa: BLE001
            pass

        tvbo_version = None
        try:
            import tvbo
            tvbo_version = getattr(tvbo, '__version__', None)
        except Exception:  # noqa: BLE001
            pass

        # Ground-truth completeness (expected vs actually-ingested, per category).
        # KG_DEGRADED when any category is below its ground-truth count — catches
        # the partial-ingest failures (graph_generator 0/9, software 0/64, …) that
        # a bare "dynamics > 0" check reports as healthy.
        try:
            from ..models.ingest import kg_completeness, registry_coverage
            completeness = kg_completeness(request.env)
            uncovered = registry_coverage()
        except Exception as e:  # noqa: BLE001
            completeness = {'verdict': 'KG_UNKNOWN', 'categories': {}, 'shortfalls': [str(e)]}
            uncovered = []

        verdict = completeness['verdict']
        # A registry category that nothing ingests means records exist in the
        # ground truth that the KG can never show (the software bug) — a config
        # defect, not healthy, even if every wired-up category is full. Fold it
        # into the verdict so the CI gate (which checks verdict==KG_OK) catches it.
        if uncovered and verdict == 'KG_OK':
            verdict = 'KG_DEGRADED'
        kg_ok = verdict == 'KG_OK'
        db_total = sum(v for v in counts.values() if isinstance(v, int))

        hint = None
        if verdict == 'KG_EMPTY':
            hint = ('Building-block tables are empty: the deploy seed_database step '
                    'did not populate the DB. Check the pod boot log for the '
                    '"TVBO KG SUMMARY" banner and any "-u tvbo" upgrade failure.')
        elif verdict == 'KG_DEGRADED':
            parts = list(completeness['shortfalls'])
            if uncovered:
                parts.append('uncovered categories: '
                             + ', '.join('%s (%s/)' % (u['category'], u['dir']) for u in uncovered)
                             + ' — add to _INGEST in models/ingest.py')
            hint = ('KG incomplete vs ground truth: ' + '; '.join(parts)
                    + '. Check /var/lib/odoo/tvbo_ingest.log for per-record FAILED lines.')

        return json_response({
            'kg_ok': kg_ok,
            'verdict': verdict,
            'completeness': completeness['categories'],
            'shortfalls': completeness['shortfalls'],
            'uncovered_categories': uncovered,
            'database_counts': counts,
            'database_total': db_total,
            'ontology_count': ontology_count,
            'tvbo_version': tvbo_version,
            'hint': hint,
        })

    # ===================
    # Main data endpoint
    # ===================

    @http.route('/tvbo/api/kg/data', type='http', auth='public', methods=['GET'], csrf=False)
    def get_all_data(self, **kw):
        """Get all knowledge graph data."""
        import traceback
        try:
            single_entity = kw.get('entity')
            if single_entity:
                if single_entity not in _KG_ENTITY_CONFIG:
                    return json_response({'error': f'Unknown entity: {single_entity}'}, 400)
                model_name = _KG_ENTITY_CONFIG[single_entity]['model']
                if _get_model_or_none(model_name) is None:
                    return json_response({'error': f'Entity model unavailable: {model_name}'}, 503)
                return json_response(self._get_entity_items(single_entity))

            include_ontology = kw.get('include_ontology', 'true').lower() != 'false'
            ontology_query = kw.get('ontology_query', '')

            data = []
            for entity_type, _, _ in _iter_available_entity_configs():
                _logger.info(f"Fetching {entity_type}...")
                data.extend(self._get_entity_items(entity_type))
                _logger.info(f"Total items: {len(data)}")

            if include_ontology:
                _logger.info("Fetching ontology concepts...")
                data.extend(self._get_ontology_concepts(ontology_query))
                _logger.info(f"Total items with ontology: {len(data)}")

            return json_response(data)
        except BaseException as e:
            tb = traceback.format_exc()
            _logger.error(f"Error in get_all_data: {e}")
            _logger.error(tb)
            try:
                return json_response({"error": str(e), "traceback": tb}, 500)
            except Exception:
                return Response(tb, content_type='text/plain', status=500)

    # ===================
    # Database serializers
    # ===================

    def _serialize_entity_row(self, entity_type, row, detail=False):
        """Serialize a database row into KG payload using schema metadata."""
        cfg = _KG_ENTITY_CONFIG[entity_type]
        data = _normalize_row(cfg['model'], row, detail=detail)

        data['type'] = entity_type
        if 'id' not in data and row.get('id') is not None:
            data['id'] = row['id']

        title = _get_display_name(data, entity_type)
        if not data.get('name'):
            data['name'] = title
        if not data.get('title'):
            data['title'] = title

        if not data.get('description') and data.get('abstract'):
            data['description'] = data.get('abstract')

        # Candidate asset names for thumbnail/report lookup. Files are named
        # after either the entity's `name`/`label`/`title`, or for networks/
        # atlases after the YAML/data_file stem (BIDS-style filenames).
        asset_candidates = []
        for key in ('name', 'label', 'method', 'title'):
            val = data.get(key)
            if isinstance(val, str) and val:
                asset_candidates.append(val)
        # data_file / file path stems (used by networks, atlases)
        for key in ('data_file', 'file', 'path', 'filename'):
            val = data.get(key)
            if isinstance(val, str) and val:
                stem = os.path.splitext(os.path.basename(val))[0]
                if stem:
                    asset_candidates.append(stem)

        # Deduplicate while preserving order
        seen_assets = set()
        asset_candidates = [a for a in asset_candidates
                            if not (a in seen_assets or seen_assets.add(a))]

        thumb_category = cfg.get('thumbnail')
        report_category = cfg.get('report')

        if thumb_category:
            for asset_name in asset_candidates:
                thumb = _thumbnail_url(thumb_category, asset_name)
                if thumb:
                    data['thumbnail'] = thumb
                    break

        if report_category:
            for asset_name in asset_candidates:
                report = _report_url(report_category, asset_name)
                if report:
                    data['report_url'] = report
                    eq_latex = _extract_equation_latex(report_category, asset_name)
                    if eq_latex:
                        data['equation_latex'] = eq_latex
                    break

        # Ontology enrichment is best-effort: it cross-links the record to ontology
        # concepts via a SPARQL label search. A record whose name/title carries
        # SPARQL-special characters (parentheses, ||, quotes — common in
        # bibliographic study titles) makes owlready2's lexer raise, which must NOT
        # take down the whole entity list. Fall back to the un-enriched row.
        try:
            return get_ontology_api().enrich_database_item(data, entity_type)
        except Exception as exc:  # noqa: BLE001
            _logger.warning("KG ontology enrichment skipped for %s '%s': %s",
                            entity_type, data.get('name') or data.get('title'), exc)
            return data

    def _get_entity_items(self, entity_type):
        """Fetch and serialize all records for one KG entity type.

        Respects model-sharing visibility: a record that is PRIVATE to another
        user (a ``tvbo.model_share`` with ``visibility='private'``) is excluded,
        so the unified Knowledge Graph shows curated ground-truth + shared
        community elements but never someone else's private model. Curated records
        have no share row and are always public; this is why shared models live in
        the KG rather than a separate gallery.
        """
        cfg = _KG_ENTITY_CONFIG[entity_type]
        if _get_model_or_none(cfg['model']) is None:
            return []
        rows = _safe_search_read(
            cfg['model'],
            _get_model_field_names(cfg['model'], include_relations=False),
            domain=self._visibility_domain(cfg['model']),
        )
        return [self._serialize_entity_row(entity_type, row, detail=False) for row in rows]

    def _visibility_domain(self, model_name):
        """Domain that hides elements private to *other* users.

        Sharing only targets models (Dynamics) and SimulationExperiments; every
        other KG entity type is curated/public and returns an empty domain.
        """
        share_field = {
            'tvbo.dynamics': 'dynamics_id',
            'tvbo.simulation_experiment': 'experiment_id',
        }.get(model_name)
        if not share_field or _get_model_or_none('tvbo.model_share') is None:
            return []
        share_dom = [('visibility', '=', 'private')]
        user = request.env.user
        if not user._is_public():
            share_dom.append(('owner_user_id', '!=', user.id))  # keep my own private models
        private = request.env['tvbo.model_share'].sudo().search(share_dom)
        private_ids = [s[share_field].id for s in private if s[share_field]]
        return [('id', 'not in', private_ids)] if private_ids else []

    def _expand_relations(self, model_name, row):
        """Expand x2many fields into nested related records for detail endpoints."""
        model = _get_model_or_none(model_name)
        if model is None:
            return {}
        expanded = {}

        for field_name, field in model._fields.items():
            if field_name not in row:
                continue
            if field.type not in ('one2many', 'many2many'):
                continue

            related_ids = row.get(field_name) or []
            if not related_ids:
                continue

            comodel_name = field.comodel_name
            related_rows = _safe_search_read(
                comodel_name,
                _get_model_field_names(comodel_name, include_relations=False),
                domain=[('id', 'in', related_ids)],
            )

            normalized_rows = [_normalize_row(comodel_name, rel_row, detail=False) for rel_row in related_rows]
            by_id = {rel_row.get('id'): rel_row for rel_row in normalized_rows}
            expanded[field_name] = [by_id[rel_id] for rel_id in related_ids if rel_id in by_id]

        return expanded

    def _get_entity_detail(self, entity_type, record_id):
        """Fetch one record with schema-driven detail serialization."""
        cfg = _KG_ENTITY_CONFIG[entity_type]
        model_name = cfg['model']
        if _get_model_or_none(model_name) is None:
            return None
        rows = _safe_search_read(
            model_name,
            _get_model_field_names(model_name, include_relations=True),
            domain=[('id', '=', record_id)],
            limit=1,
        )
        if not rows:
            return None

        row = rows[0]
        data = self._serialize_entity_row(entity_type, row, detail=True)
        data.update(self._expand_relations(model_name, row))
        return data

    def _get_dynamics(self):
        return self._get_entity_items('dynamics')

    def _get_networks(self):
        return self._get_entity_items('network')

    def _get_integrators(self):
        return self._get_entity_items('integrator')

    def _get_experiments(self):
        return self._get_entity_items('experiment')

    def _get_studies(self):
        return self._get_entity_items('study')

    def _get_couplings(self):
        return self._get_entity_items('coupling')

    def _get_observations(self):
        return self._get_entity_items('observation')

    def _get_software(self):
        return self._get_entity_items('software')

    # ===================
    # Ontology concepts
    # ===================

    def _get_ontology_concepts(self, query=''):
        api = get_ontology_api()
        concept_types = ['Model', 'NeuralMassModel', 'Coupling', 'IntegrationMethod',
                         'StateVariable', 'Parameter', 'BrainRegion', 'Parcellation',
                         'Tractogram', 'Monitor', 'Noise']

        results = []
        seen = set()

        for concept in concept_types:
            for node in api.search(concept, limit=50):
                storid = node.get('storid')
                if storid and storid not in seen:
                    seen.add(storid)
                    results.append(node)

        if query:
            for node in api.search(query, limit=50):
                storid = node.get('storid')
                if storid and storid not in seen:
                    seen.add(storid)
                    results.append(node)

        return results

    # ===================
    # Detail endpoints
    # ===================

    @http.route('/tvbo/api/kg/dynamics/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_dynamics_detail(self, record_id, **kw):
        data = self._get_entity_detail('dynamics', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)
        return json_response(data)

    @http.route('/tvbo/api/kg/network/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_network_detail(self, record_id, **kw):
        data = self._get_entity_detail('network', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)

        return json_response(data)

    @http.route('/tvbo/api/kg/integrator/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_integrator_detail(self, record_id, **kw):
        data = self._get_entity_detail('integrator', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)

        return json_response(data)

    @http.route('/tvbo/api/kg/coupling/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_coupling_detail(self, record_id, **kw):
        data = self._get_entity_detail('coupling', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)

        return json_response(data)

    @http.route('/tvbo/api/kg/experiment/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_experiment_detail(self, record_id, **kw):
        data = self._get_entity_detail('experiment', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)

        return json_response(data)

    @http.route('/tvbo/api/kg/study/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_study_detail(self, record_id, **kw):
        data = self._get_entity_detail('study', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)

        return json_response(data)

    @http.route('/tvbo/api/kg/graph_generator/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_graph_generator_detail(self, record_id, **kw):
        data = self._get_entity_detail('graph_generator', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)
        return json_response(data)

    @http.route('/tvbo/api/kg/continuation/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_continuation_detail(self, record_id, **kw):
        data = self._get_entity_detail('continuation', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)
        return json_response(data)

    @http.route('/tvbo/api/kg/observation/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_observation_detail(self, record_id, **kw):
        data = self._get_entity_detail('observation', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)

        return json_response(data)

    @http.route('/tvbo/api/kg/software/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_software_detail(self, record_id, **kw):
        data = self._get_entity_detail('software', record_id)
        if not data:
            return json_response({"error": "Not found"}, 404)

        return json_response(data)

    # ===================
    # Ontology endpoints
    # ===================

    @http.route('/tvbo/api/kg/ontology/search', type='http', auth='public', methods=['GET'], csrf=False)
    def ontology_search(self, **kw):
        """Search ontology concepts."""
        query = kw.get('q', '')
        limit = int(kw.get('limit', 100))

        if not query:
            return json_response({"error": "Missing 'q' parameter"}, 400)

        api = get_ontology_api()
        results = api.search(query, limit=limit)

        # Build graph with relationships
        nodes = results
        links = []
        seen_storids = {n.get('storid') for n in nodes if n.get('storid')}

        for node in results[:10]:
            storid = node.get('storid')
            if storid:
                rels = api.get_relationships(storid)
                for link in rels.get('links', []):
                    if link.get('source') in seen_storids and link.get('target') in seen_storids:
                        links.append(link)

        return json_response({
            "results": results,
            "graph": {"nodes": nodes, "links": links},
            "query": query
        })

    @http.route('/tvbo/api/kg/ontology/node/<int:node_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def ontology_node_detail(self, node_id, **kw):
        """Get ontology node by storid."""
        api = get_ontology_api()
        node_data = api.get_by_storid(node_id)

        if not node_data:
            return json_response({"error": "Node not found"}, 404)

        node_data['relationships'] = api.get_relationships(node_id)
        return json_response(node_data)

    @http.route('/tvbo/api/kg/ontology/node/<int:node_id>/children', type='http', auth='public', methods=['GET'], csrf=False)
    def ontology_node_children(self, node_id, **kw):
        """Get children of ontology node."""
        return json_response(get_ontology_api().get_children(node_id))

    @http.route('/tvbo/api/kg/ontology/node/<int:node_id>/parents', type='http', auth='public', methods=['GET'], csrf=False)
    def ontology_node_parents(self, node_id, **kw):
        """Get parents of ontology node."""
        return json_response(get_ontology_api().get_parents(node_id))

    @http.route('/tvbo/api/kg/ontology/graph', type='http', auth='public', methods=['GET'], csrf=False)
    def ontology_graph(self, **kw):
        """Get ontology class hierarchy."""
        return json_response(get_ontology_api().get_class_hierarchy())

    @http.route('/tvbo/api/kg/ontology/by-iri', type='http', auth='public', methods=['GET'], csrf=False)
    def ontology_by_iri(self, **kw):
        """Get ontology node by IRI."""
        iri = kw.get('iri', '')
        if not iri:
            return json_response({"error": "Missing 'iri' parameter"}, 400)

        api = get_ontology_api()
        node_data = api.get_by_iri(iri)

        if not node_data:
            return json_response({"error": "IRI not found"}, 404)

        return json_response(node_data)

    @http.route('/tvbo/api/kg/ontology/schema-link/<string:schema_class>', type='http', auth='public', methods=['GET'], csrf=False)
    def ontology_schema_link(self, schema_class, **kw):
        """Get ontology concept linked to schema class."""
        api = get_ontology_api()
        node_data = api.get_schema_ontology_link(schema_class)

        if not node_data:
            return json_response({"error": f"Schema class '{schema_class}' not linked"}, 404)

        if node_data.get('storid'):
            node_data['relationships'] = api.get_relationships(node_data['storid'])

        return json_response(node_data)

    @http.route('/tvbo/api/kg/ontology/sparql', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def ontology_sparql(self, **kw):
        """Execute SPARQL query."""
        if request.httprequest.method == 'POST':
            query_string = request.httprequest.data.decode('utf-8')
        else:
            query_string = kw.get('query', '')

        if not query_string:
            return json_response({"error": "Missing 'query' parameter"}, 400)

        api = get_ontology_api()
        results = api.sparql(query_string, flatten=False)

        serialized = []
        for row in results:
            row_data = []
            for item in row:
                if hasattr(item, 'iri'):
                    label = getattr(item, 'label', [item.name])[0] if hasattr(item, 'label') else item.name
                    row_data.append({"iri": item.iri, "label": label})
                else:
                    row_data.append(str(item) if item is not None else None)
            serialized.append(row_data)

        return json_response({"results": serialized, "count": len(serialized)})

    # ===================
    # Graph visualization endpoint
    # ===================

    @http.route('/tvbo/api/kg/graph', type='http', auth='public', methods=['GET'], csrf=False)
    def get_knowledge_graph(self, **kw):
        """Get full knowledge graph: ontology + database items with relationships.

        Optional query params:
          - limit: max ontology classes to include (default: all)
          - db_only: if 'true', only include database items, not full ontology
        """
        api = get_ontology_api()
        db_only = kw.get('db_only', 'false').lower() == 'true'
        limit = int(kw.get('limit', 0)) if kw.get('limit') else 0

        nodes = []
        links = []

        # Collect database items first so we know which ontology classes
        # they reference. Those classes must always be included regardless
        # of the requested ontology limit.
        db_items = []
        for entity_type, _, _ in _iter_available_entity_configs():
            db_items.extend(self._get_entity_items(entity_type))

        referenced_storids = set()
        for item in db_items:
            for key in ('ontology_class', 'ontology_instance'):
                ref = item.get(key)
                if ref and ref.get('storid') is not None:
                    referenced_storids.add(ref['storid'])

        # Get ontology class hierarchy (unless db_only)
        if not db_only:
            hierarchy = api.get_class_hierarchy()
            all_nodes = hierarchy.get('nodes', [])
            all_links = hierarchy.get('links', [])

            if limit > 0 and len(all_nodes) > limit:
                # Keep referenced classes plus the first `limit` other classes.
                kept = []
                kept_ids = set()
                for n in all_nodes:
                    sid = n.get('storid')
                    if sid in referenced_storids and sid not in kept_ids:
                        kept.append(n)
                        kept_ids.add(sid)
                for n in all_nodes:
                    if len(kept) >= limit:
                        break
                    sid = n.get('storid')
                    if sid not in kept_ids:
                        kept.append(n)
                        kept_ids.add(sid)
                nodes = kept
                links = [l for l in all_links
                         if l.get('source') in kept_ids and l.get('target') in kept_ids]
            else:
                nodes = all_nodes
                links = all_links

        # Map database items to nodes and create links to ontology
        onto_storid_map = {n['storid']: n for n in nodes if n.get('storid') is not None}

        for item in db_items:
            node_id = f"db_{item['type']}_{item['id']}"
            node = {
                'id': node_id,
                'storid': node_id,
                'label': item.get('name') or item.get('label') or item.get('title', ''),
                'type': 'instance',
                'db_type': item['type'],
                'title': item.get('title', ''),
                'iri': item.get('iri', ''),
            }
            nodes.append(node)

            # Link to specific ontology instance if available, else to class.
            onto_class = item.get('ontology_class')
            onto_instance = item.get('ontology_instance')

            target_storid = None
            if onto_instance and onto_instance.get('storid') is not None:
                target_storid = onto_instance['storid']
            elif onto_class and onto_class.get('storid') is not None:
                target_storid = onto_class['storid']

            if target_storid is not None and target_storid in onto_storid_map:
                links.append({
                    'source': node_id,
                    'target': target_storid,
                    'type': 'instance_of',
                    'label': 'instance of',
                })

        return json_response({
            "nodes": nodes,
            "links": links,
            "stats": {
                "ontology_classes": len([n for n in nodes if n.get('type') != 'instance']),
                "database_items": len(db_items),
                "total_nodes": len(nodes),
                "total_links": len(links),
            }
        })
