# -*- coding: utf-8 -*-
"""
Building-blocks API for the schema-driven experiment configurator.

Three responsibilities:

1. /tvbo/api/configurator/schema
   Parsed LinkML schema (tvbo_datamodel.yaml + imports), JSON-friendly,
   used by the JS form generator.

2. /tvbo/api/configurator/instances/<class>[/<id>]
   List / fetch / create reusable library instances of any schema class
   that has a corresponding Odoo model. Powers the ClassPicker UI.

3. /tvbo/api/configurator/experiment/serialize  (POST)
   Round-trips arbitrary experiment JSON through Pydantic and returns
   schema-correct YAML. Single source of truth for the live preview and
   the YAML download button.
"""
import json
import logging
import re

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json(data, status=200):
    return request.make_response(
        json.dumps(data, default=str),
        headers=[('Content-Type', 'application/json')],
        status=status,
    )


def _camel_to_snake(name):
    """`SimulationExperiment` -> `simulation_experiment`."""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _class_to_odoo_model(class_name):
    """`Dynamics` -> `tvbo.dynamics`. Returns None if no such model exists."""
    model_name = f'tvbo.{_camel_to_snake(class_name)}'
    if model_name in request.env:
        return model_name
    return None


# ---------------------------------------------------------------------------
# Schema cache (process-local)
# ---------------------------------------------------------------------------

_SCHEMA_CACHE = {'json': None}


def _locate_schema_file():
    """Find tvbo_datamodel.yaml across the layouts the container may use."""
    import os
    candidates = []
    try:
        import tvbo
        tvbo_dir = os.path.dirname(tvbo.__file__)
        candidates.append(os.path.join(tvbo_dir, 'schema', 'tvbo_datamodel.yaml'))
        candidates.append(os.path.join(os.path.dirname(tvbo_dir), 'schema', 'tvbo_datamodel.yaml'))
    except Exception:
        pass
    candidates += [
        '/tmp/tvbo/schema/tvbo_datamodel.yaml',
        '/tmp/tvbo/tvbo/schema/tvbo_datamodel.yaml',
        '/tvbo/schema/tvbo_datamodel.yaml',
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def _build_schema_json():
    """Resolve LinkML schema to a compact JSON form usable by the JS UI."""
    from linkml_runtime.utils.schemaview import SchemaView

    schema_path = _locate_schema_file()
    if schema_path is None:
        raise FileNotFoundError(
            'tvbo_datamodel.yaml not found (tried package data, /tmp/tvbo/schema, /tvbo/schema)'
        )

    sv = SchemaView(schema_path)

    classes_out = {}
    for class_name, cls in sv.all_classes().items():
        slots = {}
        for slot_name in sv.class_slots(class_name):
            slot = sv.induced_slot(slot_name, class_name)
            slots[slot_name] = {
                'name': slot.name,
                'alias': slot.alias,
                'range': slot.range,
                'multivalued': bool(slot.multivalued),
                'required': bool(slot.required),
                'identifier': bool(slot.identifier),
                'inlined': bool(slot.inlined),
                'inlined_as_list': bool(slot.inlined_as_list),
                'description': slot.description or '',
                'ifabsent': slot.ifabsent,
                'pattern': slot.pattern,
                'minimum_value': slot.minimum_value,
                'maximum_value': slot.maximum_value,
                'unit': getattr(slot, 'unit', None) and getattr(slot.unit, 'ucum_code', None),
                'deprecated': slot.deprecated,
            }
        odoo_model = _class_to_odoo_model(class_name)
        classes_out[class_name] = {
            'name': class_name,
            'description': cls.description or '',
            'is_a': cls.is_a,
            'mixins': list(cls.mixins or []),
            'tree_root': bool(cls.tree_root),
            'abstract': bool(cls.abstract),
            'slots': slots,
            'odoo_model': odoo_model,
            'pickable': odoo_model is not None,
        }

    enums_out = {}
    for enum_name, enum in sv.all_enums().items():
        enums_out[enum_name] = {
            'name': enum_name,
            'description': enum.description or '',
            'permissible_values': {
                pv_name: {
                    'text': pv.text,
                    'description': pv.description or '',
                    'meaning': pv.meaning,
                }
                for pv_name, pv in (enum.permissible_values or {}).items()
            },
        }

    types_out = {
        type_name: {
            'name': type_name,
            'base': t.base,
            'uri': t.uri,
            'description': t.description or '',
        }
        for type_name, t in sv.all_types().items()
    }

    return {
        'name': sv.schema.name,
        'version': sv.schema.version,
        'classes': classes_out,
        'enums': enums_out,
        'types': types_out,
    }


def _get_schema_json(force=False):
    if force or _SCHEMA_CACHE['json'] is None:
        _SCHEMA_CACHE['json'] = _build_schema_json()
    return _SCHEMA_CACHE['json']


# ---------------------------------------------------------------------------
# Deep record resolver (mirrors model_configurator._resolve_record_deep but
# kept local to avoid a circular controller import).
# ---------------------------------------------------------------------------

_SKIP_FIELDS = {
    'id', 'display_name', 'create_uid', 'create_date',
    'write_uid', 'write_date', '__last_update', 'record_id',
}


def _clean(value):
    """Recursively drop Odoo's ``False`` placeholders and metadata keys,
    leaving a JSON / YAML-friendly structure.
    """
    if value is False or value is None:
        return None
    if isinstance(value, list):
        cleaned = [_clean(v) for v in value]
        cleaned = [v for v in cleaned if v not in (None, {}, [])]
        return cleaned
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in _SKIP_FIELDS:
                continue
            cv = _clean(v)
            if cv is None or cv == [] or cv == {}:
                continue
            out[k] = cv
        return out
    return value


def _resolve_record_deep(record, depth=4):
    if not record or depth <= 0:
        return None
    data = record.read()[0]
    for field_name, field_obj in record._fields.items():
        if field_name in _SKIP_FIELDS:
            continue
        value = getattr(record, field_name, None)
        if not value:
            continue
        if field_obj.type == 'many2one':
            data[field_name] = _resolve_record_deep(value, depth - 1)
        elif field_obj.type in ('many2many', 'one2many'):
            data[field_name] = [
                _resolve_record_deep(r, depth - 1) for r in value
            ]
    return data


def _record_summary(record):
    """Lightweight projection for ClassPicker dropdown entries."""
    return {
        'id': record.id,
        'name': getattr(record, 'name', None) or getattr(record, 'label', None) or str(record.id),
        'label': getattr(record, 'label', None) or getattr(record, 'name', None) or str(record.id),
        'description': (getattr(record, 'description', None) or '')[:240],
    }


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class BuildingBlocksController(http.Controller):

    # ---- 1. Schema ----------------------------------------------------------
    @http.route(
        '/tvbo/api/configurator/schema',
        type='http', auth='public', methods=['GET'], csrf=False,
    )
    def api_schema(self, refresh=None, **kwargs):
        try:
            schema = _get_schema_json(force=bool(refresh))
            return _json({'success': True, 'data': schema})
        except Exception as e:
            _logger.error('schema endpoint failed: %s', e, exc_info=True)
            return _json({'success': False, 'error': str(e)}, status=500)

    # ---- 2. Instances -------------------------------------------------------
    @http.route(
        '/tvbo/api/configurator/instances/<string:class_name>',
        type='http', auth='public', methods=['GET'], csrf=False,
    )
    def api_instances_list(self, class_name, q=None, limit='200', **kwargs):
        try:
            model_name = _class_to_odoo_model(class_name)
            if not model_name:
                return _json({'success': False, 'error': f'No DB model for class {class_name}'}, status=404)
            domain = []
            if q:
                domain = ['|', '|',
                          ('name', 'ilike', q),
                          ('label', 'ilike', q) if 'label' in request.env[model_name]._fields else ('name', 'ilike', q),
                          ('description', 'ilike', q) if 'description' in request.env[model_name]._fields else ('name', 'ilike', q)]
            try:
                lim = int(limit)
            except ValueError:
                lim = 200
            records = request.env[model_name].sudo().search(domain, limit=lim)
            return _json({
                'success': True,
                'class': class_name,
                'odoo_model': model_name,
                'count': len(records),
                'data': [_record_summary(r) for r in records],
            })
        except Exception as e:
            _logger.error('instances list failed for %s: %s', class_name, e, exc_info=True)
            return _json({'success': False, 'error': str(e)}, status=500)

    @http.route(
        '/tvbo/api/configurator/instances/<string:class_name>/<int:rec_id>',
        type='http', auth='public', methods=['GET'], csrf=False,
    )
    def api_instance_detail(self, class_name, rec_id, depth='4', **kwargs):
        try:
            model_name = _class_to_odoo_model(class_name)
            if not model_name:
                return _json({'success': False, 'error': f'No DB model for class {class_name}'}, status=404)
            try:
                d = max(1, min(8, int(depth)))
            except ValueError:
                d = 4
            rec = request.env[model_name].sudo().browse(rec_id)
            if not rec.exists():
                return _json({'success': False, 'error': 'Not found'}, status=404)
            return _json({
                'success': True,
                'class': class_name,
                'odoo_model': model_name,
                'data': _resolve_record_deep(rec, depth=d),
            })
        except Exception as e:
            _logger.error('instance detail failed: %s', e, exc_info=True)
            return _json({'success': False, 'error': str(e)}, status=500)

    @http.route(
        '/tvbo/api/configurator/instances/<string:class_name>',
        type='json', auth='user', methods=['POST'], csrf=False,
    )
    def api_instance_create(self, class_name, **kwargs):
        """Save a customised building block back to the library.

        Expects a JSON body whose top-level keys are the scalar (writable)
        fields of the target Odoo model. Relational fields are intentionally
        not auto-created here — pick existing instances or call this endpoint
        recursively from the client.
        """
        try:
            model_name = _class_to_odoo_model(class_name)
            if not model_name:
                return {'success': False, 'error': f'No DB model for class {class_name}'}
            payload = kwargs.get('data') or {}
            if not isinstance(payload, dict):
                return {'success': False, 'error': 'data must be an object'}

            Model = request.env[model_name].sudo()
            # Only keep scalar fields the model actually has, to avoid create errors.
            create_vals = {}
            for k, v in payload.items():
                if k in Model._fields and Model._fields[k].type in (
                    'char', 'text', 'integer', 'float', 'boolean', 'date',
                    'datetime', 'selection', 'html',
                ):
                    create_vals[k] = v
            # Many2one references by id (single int)
            for k, v in payload.items():
                if k in Model._fields and Model._fields[k].type == 'many2one' and isinstance(v, int):
                    create_vals[k] = v
            # Many2many / one2many references as list[int]
            for k, v in payload.items():
                if k in Model._fields and Model._fields[k].type in ('many2many', 'one2many') \
                        and isinstance(v, list) and all(isinstance(x, int) for x in v):
                    create_vals[k] = [(6, 0, v)]

            rec = Model.create(create_vals)
            return {
                'success': True,
                'class': class_name,
                'odoo_model': model_name,
                'id': rec.id,
                'data': _record_summary(rec),
            }
        except Exception as e:
            _logger.error('instance create failed: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ---- 3. Serialize -------------------------------------------------------
    @http.route(
        '/tvbo/api/configurator/experiment/serialize',
        type='json', auth='public', methods=['POST'], csrf=False,
    )
    def api_experiment_serialize(self, **kwargs):
        """Convert raw experiment JSON to schema-correct YAML via Pydantic.

        Body: { "experiment": {...}, "format": "yaml"|"json" (default yaml) }
        """
        try:
            from tvbo.datamodel.tvbopydantic import SimulationExperiment
            from pydantic import ValidationError
            import yaml

            payload = kwargs.get('experiment')
            if payload is None:
                return {'success': False, 'error': 'experiment is required'}
            if not isinstance(payload, dict):
                return {'success': False, 'error': 'experiment must be an object'}

            fmt = (kwargs.get('format') or 'yaml').lower()

            try:
                exp = SimulationExperiment.model_validate(payload)
            except ValidationError as ve:
                return {
                    'success': False,
                    'error': 'validation_error',
                    'errors': ve.errors(),
                }

            data = exp.model_dump(exclude_none=True, exclude_unset=False)
            wrapped = {'simulation_experiment': data}
            if fmt == 'json':
                return {'success': True, 'format': 'json', 'data': wrapped}
            return {
                'success': True,
                'format': 'yaml',
                'yaml': yaml.dump(
                    wrapped, default_flow_style=False,
                    sort_keys=False, allow_unicode=True,
                ),
            }
        except ImportError as e:
            _logger.error('tvbo package missing: %s', e)
            return {'success': False, 'error': 'tvbo Python package not installed'}
        except Exception as e:
            _logger.error('serialize failed: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ---- 4. Raw YAML dump (no Pydantic validation) --------------------------
    # Pragmatic path used by the configurator's live preview pane and the
    # YAML download button: take whatever shape the database (or the JS
    # state) gives us, clean it, and dump it as YAML. This guarantees we
    # never lose fields just because they don't pass Pydantic strict
    # validation (e.g. units that aren't yet in the enum, empty Odoo
    # ``False`` placeholders, lists where the schema declares a dict).
    @http.route(
        '/tvbo/api/configurator/experiment/<int:rec_id>/yaml_raw',
        type='http', auth='public', methods=['GET'], csrf=False,
    )
    def api_experiment_yaml_raw(self, rec_id, depth='6', **kwargs):
        try:
            import yaml
            try:
                d = max(1, min(8, int(depth)))
            except ValueError:
                d = 6
            rec = request.env['tvbo.simulation_experiment'].sudo().browse(rec_id)
            if not rec.exists():
                return _json({'success': False, 'error': 'Not found'}, status=404)
            data = _clean(_resolve_record_deep(rec, depth=d)) or {}
            wrapped = {'simulation_experiment': data}
            return request.make_response(
                yaml.dump(
                    wrapped, default_flow_style=False,
                    sort_keys=False, allow_unicode=True,
                ),
                headers=[('Content-Type', 'application/x-yaml; charset=utf-8')],
            )
        except Exception as e:
            _logger.error('yaml_raw failed: %s', e, exc_info=True)
            return _json({'success': False, 'error': str(e)}, status=500)

    @http.route(
        '/tvbo/api/configurator/experiment/dump_yaml',
        type='json', auth='public', methods=['POST'], csrf=False,
    )
    def api_experiment_dump_yaml(self, **kwargs):
        """Same as yaml_raw but takes the JSON state in the request body.

        Used by the live preview after the user has edited fields locally.
        """
        try:
            import yaml
            payload = kwargs.get('experiment')
            if payload is None:
                return {'success': False, 'error': 'experiment is required'}
            data = _clean(payload) or {}
            wrapped = {'simulation_experiment': data}
            return {
                'success': True,
                'yaml': yaml.dump(
                    wrapped, default_flow_style=False,
                    sort_keys=False, allow_unicode=True,
                ),
            }
        except Exception as e:
            _logger.error('dump_yaml failed: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
