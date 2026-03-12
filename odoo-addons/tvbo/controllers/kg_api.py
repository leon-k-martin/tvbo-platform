# -*- coding: utf-8 -*-
"""
Knowledge Graph API - Clean MVP implementation.
No fallbacks. Fails fast when something unexpected happens.
"""
import json
import logging
import os

from odoo import http
from odoo.http import Response, request

from tvbo.datamodel.tvbopydantic import Coupling as PydanticCoupling
from tvbo.datamodel.tvbopydantic import Dynamics as PydanticDynamics
from tvbo.datamodel.tvbopydantic import Integrator as PydanticIntegrator
from tvbo.datamodel.tvbopydantic import Network as PydanticNetwork
from tvbo.datamodel.tvbopydantic import SimulationExperiment as PydanticSimulationExperiment
from tvbo.datamodel.tvbopydantic import SimulationStudy as PydanticSimulationStudy
from tvbo.api.direct_ontology_api import get_direct_ontology_api

_logger = logging.getLogger(__name__)

# Singleton ontology API
_ontology_api = None

# Thumbnail directory (static files in the addon)
_THUMB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'src', 'img', 'thumbnails')
_THUMB_URL = '/tvbo/static/src/img/thumbnails'

# Report directory (pre-rendered markdown)
_REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'src', 'reports')
_REPORT_URL = '/tvbo/static/src/reports'


def _thumbnail_url(category: str, name: str) -> str | None:
    """Return the URL for a thumbnail if it exists on disk."""
    png = os.path.join(_THUMB_DIR, category, f'{name}.png')
    if os.path.isfile(png):
        return f'{_THUMB_URL}/{category}/{name}.png'
    return None


def _report_url(category: str, name: str) -> str | None:
    """Return the URL for a pre-rendered report if it exists on disk."""
    md = os.path.join(_REPORT_DIR, category, f'{name}.md')
    if os.path.isfile(md):
        return f'{_REPORT_URL}/{category}/{name}.md'
    return None


def get_ontology_api():
    """Get DirectOntologyAPI singleton. Fails if unavailable."""
    global _ontology_api
    if _ontology_api is None:
        _ontology_api = get_direct_ontology_api()
    return _ontology_api


def json_response(data, status=200):
    """Standard JSON response with CORS."""
    return Response(
        json.dumps(data),
        content_type='application/json',
        status=status,
        headers={'Access-Control-Allow-Origin': '*'}
    )


def _field_label(field_name):
    """Convert field_name to a human-readable label."""
    return field_name.replace('_', ' ').title()


def _introspect_field(field_name, field_info):
    """Return field schema dict if the field is filterable, None otherwise.

    Filterable = simple scalar types (str, int, float, bool, enum).
    Skips nested objects, lists, dicts, and internal fields.
    """
    from typing import get_origin, get_args, Union
    from enum import Enum

    annotation = field_info.annotation
    base_type = annotation

    # Unwrap Optional[T]
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            base_type = non_none[0]
            origin = get_origin(base_type)
        else:
            return None

    # Skip list, dict, and other generic container types
    if origin in (list, dict, set, frozenset):
        return None

    # Extract description from field metadata
    desc = field_info.description or ''

    if base_type is str:
        return {'type': 'string', 'label': _field_label(field_name), 'description': desc}
    elif base_type in (int, float):
        return {'type': 'number', 'label': _field_label(field_name), 'description': desc}
    elif base_type is bool:
        return {'type': 'boolean', 'label': _field_label(field_name), 'description': desc}
    elif isinstance(base_type, type) and issubclass(base_type, Enum):
        values = [{'value': v.value, 'label': v.name} for v in base_type]
        return {'type': 'enum', 'label': _field_label(field_name), 'description': desc, 'values': values}

    # Skip complex types (Pydantic models, etc.)
    return None


class KnowledgeGraphAPI(http.Controller):
    """Knowledge Graph API endpoints. Clean MVP."""

    # ===================
    # Schema
    # ===================

    @http.route('/tvbo/api/kg/schema', type='http', auth='public', methods=['GET'], csrf=False)
    def get_schema(self, **kw):
        """Get browser schema configuration."""
        return json_response({
            "searchableFields": ["name", "label", "title", "description", "abstract", "doi", "method", "definition", "symbol"],
            "facets": [
                {"field": "type", "label": "Class", "type": "string"},
            ],
            "sources": ["database", "ontology"]
        })

    @http.route('/tvbo/api/kg/schema/classes', type='http', auth='public', methods=['GET'], csrf=False)
    def get_class_schemas(self, **kw):
        """Get schemas for all datamodel classes represented in the KG.

        Introspects Pydantic models (generated from tvbo_datamodel.yaml) to return
        class names, descriptions, and filterable properties with types.
        """
        from tvbo.datamodel import tvbopydantic as dm
        from typing import get_origin, get_args, Union
        from enum import Enum

        # Map KG type values to Pydantic classes — the only hardcoded part.
        # Everything else is introspected from the schema.
        type_class_map = {
            'dynamics': dm.Dynamics,
            'network': dm.Network,
            'integrator': dm.Integrator,
            'experiment': dm.SimulationExperiment,
            'study': dm.SimulationStudy,
            'coupling': dm.Coupling,
        }

        result = {}
        for type_key, cls in type_class_map.items():
            properties = {}
            for field_name, field_info in cls.model_fields.items():
                if field_name == 'linkml_meta':
                    continue
                prop = _introspect_field(field_name, field_info)
                if prop:
                    properties[field_name] = prop

            # Use the class name as the label (not LinkML aliases, which may be deprecated)
            class_label = cls.__name__

            result[type_key] = {
                'class_name': cls.__name__,
                'label': class_label,
                'description': (cls.__doc__ or '').strip(),
                'properties': properties,
            }

        return json_response(result)

    # ===================
    # Main data endpoint
    # ===================

    @http.route('/tvbo/api/kg/data', type='http', auth='public', methods=['GET'], csrf=False)
    def get_all_data(self, **kw):
        """Get all knowledge graph data."""
        import traceback
        try:
            include_ontology = kw.get('include_ontology', 'true').lower() != 'false'
            ontology_query = kw.get('ontology_query', '')

            data = []
            _logger.info("Fetching dynamics...")
            data.extend(self._get_dynamics())
            _logger.info(f"Got {len(data)} dynamics")
            _logger.info("Fetching networks...")
            data.extend(self._get_networks())
            _logger.info(f"Total items: {len(data)}")
            _logger.info("Fetching integrators...")
            data.extend(self._get_integrators())
            _logger.info(f"Total items: {len(data)}")
            _logger.info("Fetching experiments...")
            data.extend(self._get_experiments())
            _logger.info(f"Total items: {len(data)}")
            _logger.info("Fetching studies...")
            data.extend(self._get_studies())
            _logger.info(f"Total items: {len(data)}")
            _logger.info("Fetching couplings...")
            data.extend(self._get_couplings())
            _logger.info(f"Total items: {len(data)}")

            if include_ontology:
                _logger.info("Fetching ontology concepts...")
                data.extend(self._get_ontology_concepts(ontology_query))
                _logger.info(f"Total items with ontology: {len(data)}")

            return json_response(data)
        except Exception as e:
            _logger.error(f"Error in get_all_data: {e}")
            _logger.error(traceback.format_exc())
            return json_response({"error": str(e), "traceback": traceback.format_exc()}, 500)

    # ===================
    # Database serializers
    # ===================

    def _get_dynamics(self):
        records = request.env['tvbo.dynamics'].sudo().search([])
        return [self._serialize_dynamics(r) for r in records]

    def _serialize_dynamics(self, record):
        result = PydanticDynamics(
            name=record.name or 'Unknown',
            label=record.label or None,
            description=record.description or None,
            source=record.source or None,
            iri=record.iri or None,
        ).model_dump(exclude_none=True)

        result.update({
            'id': record.id,
            'type': 'dynamics',
            'title': record.name or record.label or '',
            'system_type': record.system_type.technical_name if record.system_type else '',
        })

        thumb = _thumbnail_url('models', record.name or '')
        if thumb:
            result['thumbnail'] = thumb

        report = _report_url('models', record.name or '')
        if report:
            result['report_url'] = report

        return get_ontology_api().enrich_database_item(result, 'dynamics')

    def _get_networks(self):
        records = request.env['tvbo.network'].sudo().search([])
        return [self._serialize_network(r) for r in records]

    def _serialize_network(self, record):
        result = PydanticNetwork(
            label=record.label or None,
            description=record.description or None,
            number_of_nodes=record.number_of_nodes or record.number_of_regions or 1,
        ).model_dump(exclude_none=True)

        result.update({
            'id': record.id,
            'type': 'network',
            'name': record.label or f'Network {record.id}',
            'title': record.label or f'Network {record.id}',
        })

        # Try thumbnail by label
        thumb = _thumbnail_url('networks', record.label or '')
        if thumb:
            result['thumbnail'] = thumb

        return get_ontology_api().enrich_database_item(result, 'network')

    def _get_integrators(self):
        records = request.env['tvbo.integrator'].sudo().search([])
        return [self._serialize_integrator(r) for r in records]

    def _serialize_integrator(self, record):
        result = PydanticIntegrator(
            method=record.method or None,
            step_size=record.step_size or 0.01220703125,
            duration=record.duration or 1000.0,
            time_scale=record.time_scale or 'ms',
        ).model_dump(exclude_none=True)

        result.update({
            'id': record.id,
            'type': 'integrator',
            'name': record.method or f'Integrator {record.id}',
            'title': record.method or f'Integrator {record.id}',
            'description': f"Method: {record.method}, Step: {record.step_size}, Duration: {record.duration}",
        })

        report = _report_url('integrators', record.method or '')
        if report:
            result['report_url'] = report

        return get_ontology_api().enrich_database_item(result, 'integrator')

    def _get_experiments(self):
        records = request.env['tvbo.simulation_experiment'].sudo().search([])
        return [self._serialize_experiment(r) for r in records]

    def _serialize_experiment(self, record):
        result = PydanticSimulationExperiment(
            id=str(record.id),
            label=record.label or None,
            description=record.description or None,
        ).model_dump(exclude_none=True)

        result.update({
            'id': record.id,
            'type': 'experiment',
            'name': record.label or f'Experiment {record.id}',
            'title': record.label or f'Experiment {record.id}',
            'abstract': record.description or '',
        })

        return get_ontology_api().enrich_database_item(result, 'experiment')

    def _get_studies(self):
        records = request.env['tvbo.simulation_study'].sudo().search([])
        return [self._serialize_study(r) for r in records]

    def _serialize_study(self, record):
        result = PydanticSimulationStudy(
            label=record.label or None,
            description=record.description or None,
            doi=record.doi or None,
            title=record.title or None,
        ).model_dump(exclude_none=True)

        result.update({
            'id': record.id,
            'type': 'study',
            'name': record.title or record.label or f'Study {record.id}',
            'title': record.title or record.label or f'Study {record.id}',
            'abstract': record.description or '',
            'year': str(record.year) if record.year else '',
            'doi': record.doi or '',
        })

        return get_ontology_api().enrich_database_item(result, 'study')

    def _get_couplings(self):
        records = request.env['tvbo.coupling'].sudo().search([])
        return [self._serialize_coupling(r) for r in records]

    def _serialize_coupling(self, record):
        result = PydanticCoupling(
            name=record.name or 'Linear',
            label=record.label or None,
            delayed=record.delayed,
            sparse=record.sparse,
        ).model_dump(exclude_none=True)

        # Build equation display from pre/post expressions
        eq_parts = []
        if record.pre_expression and record.pre_expression.righthandside:
            eq_parts.append(f'pre(x_j) = {record.pre_expression.righthandside}')
        if record.post_expression and record.post_expression.righthandside:
            eq_parts.append(f'post(gx) = {record.post_expression.righthandside}')

        result.update({
            'id': record.id,
            'type': 'coupling',
            'title': record.name or record.label or f'Coupling {record.id}',
            'description': record.coupling_function.definition if record.coupling_function else '',
            'equation': ' ;  '.join(eq_parts) if eq_parts else '',
        })

        thumb = _thumbnail_url('coupling_functions', record.name or '')
        if thumb:
            result['thumbnail'] = thumb

        report = _report_url('coupling_functions', record.name or '')
        if report:
            result['report_url'] = report

        return get_ontology_api().enrich_database_item(result, 'coupling')

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
        record = request.env['tvbo.dynamics'].sudo().browse(record_id)
        if not record.exists():
            return json_response({"error": "Not found"}, 404)

        data = self._serialize_dynamics(record)
        data['parameters'] = [{
            "name": p.name, "label": p.label, "symbol": p.symbol or '',
            "value": p.value, "description": p.description or ''
        } for p in record.parameters]
        data['state_variables'] = [{
            "name": sv.name, "label": sv.label, "symbol": sv.symbol or '',
            "description": sv.description or '',
            "equation": {"label": sv.equation.label, "definition": sv.equation.definition} if sv.equation else None
        } for sv in record.state_variables]

        return json_response(data)

    @http.route('/tvbo/api/kg/network/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_network_detail(self, record_id, **kw):
        record = request.env['tvbo.network'].sudo().browse(record_id)
        if not record.exists():
            return json_response({"error": "Not found"}, 404)

        data = self._serialize_network(record)
        if record.parcellation:
            data['parcellation'] = {"label": record.parcellation.label, "data_source": record.parcellation.data_source}

        return json_response(data)

    @http.route('/tvbo/api/kg/integrator/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_integrator_detail(self, record_id, **kw):
        record = request.env['tvbo.integrator'].sudo().browse(record_id)
        if not record.exists():
            return json_response({"error": "Not found"}, 404)

        data = self._serialize_integrator(record)
        data['parameters'] = [{
            "name": p.name, "label": p.label, "symbol": p.symbol or '',
            "value": p.value, "description": p.description or ''
        } for p in record.parameters]

        return json_response(data)

    @http.route('/tvbo/api/kg/coupling/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_coupling_detail(self, record_id, **kw):
        record = request.env['tvbo.coupling'].sudo().browse(record_id)
        if not record.exists():
            return json_response({"error": "Not found"}, 404)

        data = self._serialize_coupling(record)
        if record.coupling_function:
            data['coupling_function'] = {"label": record.coupling_function.label, "definition": record.coupling_function.definition}
        data['parameters'] = [{
            "name": p.name, "label": p.label, "symbol": p.symbol or '',
            "value": p.value, "description": p.description or ''
        } for p in record.parameters]

        return json_response(data)

    @http.route('/tvbo/api/kg/experiment/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_experiment_detail(self, record_id, **kw):
        record = request.env['tvbo.simulation_experiment'].sudo().browse(record_id)
        if not record.exists():
            return json_response({"error": "Not found"}, 404)

        data = self._serialize_experiment(record)
        if record.dynamics:
            data['dynamics'] = {"id": record.dynamics.id, "name": record.dynamics.name}
        if record.integration:
            data['integration'] = {"id": record.integration.id, "method": record.integration.method}
        if record.connectivity:
            data['connectivity'] = {"id": record.connectivity.id, "label": record.connectivity.label}

        return json_response(data)

    @http.route('/tvbo/api/kg/study/<int:record_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_study_detail(self, record_id, **kw):
        record = request.env['tvbo.simulation_study'].sudo().browse(record_id)
        if not record.exists():
            return json_response({"error": "Not found"}, 404)

        return json_response(self._serialize_study(record))

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

        # Get ontology class hierarchy (unless db_only)
        if not db_only:
            hierarchy = api.get_class_hierarchy()
            nodes = hierarchy.get('nodes', [])
            links = hierarchy.get('links', [])

            # Apply limit if specified
            if limit > 0 and len(nodes) > limit:
                nodes = nodes[:limit]
                # Filter links to only include nodes in our limited set
                node_ids = {n.get('storid') for n in nodes}
                links = [l for l in links if l.get('source') in node_ids and l.get('target') in node_ids]

        # Add database items as nodes linked to their ontology classes
        db_items = []
        db_items.extend(self._get_dynamics())
        db_items.extend(self._get_networks())
        db_items.extend(self._get_integrators())
        db_items.extend(self._get_experiments())
        db_items.extend(self._get_studies())
        db_items.extend(self._get_couplings())

        # Map database items to nodes and create links to ontology
        onto_storid_map = {n['storid']: n for n in nodes if n.get('storid')}

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

            # Link to ontology class if enriched (check ontology_class.storid or ontology_instance.storid)
            onto_class = item.get('ontology_class')
            onto_instance = item.get('ontology_instance')

            # Try to link to specific instance first, then to class
            target_storid = None
            if onto_instance and onto_instance.get('storid'):
                target_storid = onto_instance['storid']
            elif onto_class and onto_class.get('storid'):
                target_storid = onto_class['storid']

            if target_storid and target_storid in onto_storid_map:
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
