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
import logging
import re

from odoo import http
from odoo.http import request

from .assets import json_payload

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json(data, status=200):
    return json_payload(data, status=status)


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

# Pure ORM bookkeeping to strip from resolved data. Crucially this does NOT
# include the reserved-renamed schema slots (``record_id`` -> ``id``,
# ``is_modified`` -> ``modified``): those carry real schema values and are
# restored by ``_rename_reserved`` after cleaning.
_ODOO_METADATA = {
    'id', 'display_name', 'create_uid', 'create_date',
    'write_uid', 'write_date', '__last_update',
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
            if k in _ODOO_METADATA:
                continue
            cv = _clean(v)
            if cv is None or cv == [] or cv == {}:
                continue
            out[k] = cv
        return out
    return value


# Field-name divergences between the platform's generated Odoo models and the
# current tvbo Pydantic datamodel. Invert them when turning Odoo records back
# into schema-shaped data. (See todo.md: the durable fix is to regenerate the
# Odoo models + seed from the current tvbo schema so these vanish.)
#   record_id/is_modified : reserved ORM names (generate_odoo_models)
#   lefthandside/righthandside : Equation slots renamed to lhs/rhs upstream
_ODOO_RESERVED_INVERSE = {
    'record_id': 'id',
    'is_modified': 'modified',
    'lefthandside': 'lhs',
    'righthandside': 'rhs',
}


def _rename_reserved(value):
    """Recursively restore schema slot names from Odoo's field-name renames."""
    if isinstance(value, list):
        return [_rename_reserved(v) for v in value]
    if isinstance(value, dict):
        return {
            _ODOO_RESERVED_INVERSE.get(k, k): _rename_reserved(v)
            for k, v in value.items()
        }
    return value


def _flatten_parent_links(value):
    """Flatten Odoo inheritance parent-links into their owner.

    ``generate_odoo_models`` models LinkML ``is_a`` inheritance as a
    ``<parent>_id`` Many2one holding the inherited slots (e.g. an Integrator's
    Solver fields live under ``solver_id``). The schema inlines those slots, so
    we merge any ``*_id`` whose value is a (resolved) record dict up into its
    owner — the owner's own keys win on collision.
    """
    if isinstance(value, list):
        return [_flatten_parent_links(v) for v in value]
    if not isinstance(value, dict):
        return value
    merged = {}
    own = {}
    for k, v in value.items():
        v = _flatten_parent_links(v)
        if k.endswith('_id') and isinstance(v, dict):
            merged.update(v)  # inherited fields (lowest priority)
        else:
            own[k] = v
    merged.update(own)  # owner's own fields win
    return merged


def _is_enum_model(recordset):
    """Enum lookup models (generated as name/technical_name/description) are the
    only models carrying a ``technical_name`` field — used to collapse enum
    relations back to their permissible-value string on export."""
    return 'technical_name' in recordset._fields and 'name' in recordset._fields


def _resolve_record_deep(record, depth=8, _seen=None, _memo=None):
    """Deep-resolve an Odoo record to a nested dict.

    Uses a memo (resolve each record once, deep-copy on reuse) so shared records
    referenced from many places aren't re-resolved combinatorially, plus a
    path-scoped ``_seen`` set to break reference cycles. This keeps complex
    experiments (e.g. bifurcation continuations that re-reference a Dynamics)
    fast instead of exploding.
    """
    import copy as _copy
    if not record or depth <= 0:
        return None
    if _seen is None:
        _seen = set()
    if _memo is None:
        _memo = {}
    key = (record._name, record.id)
    if key in _memo:
        return _copy.deepcopy(_memo[key])
    if key in _seen:
        # Reference cycle: return a shallow reference instead of recursing forever.
        return {'name': record.name} if 'name' in record._fields else None
    _seen.add(key)
    try:
        data = record.read()[0]
        for field_name, field_obj in record._fields.items():
            if field_name in _SKIP_FIELDS:
                continue
            value = getattr(record, field_name, None)
            if not value:
                continue
            if field_obj.type == 'many2one':
                # Enum relation -> the permissible-value string the schema expects.
                data[field_name] = value.name if _is_enum_model(value) else _resolve_record_deep(value, depth - 1, _seen, _memo)
            elif field_obj.type in ('many2many', 'one2many'):
                if _is_enum_model(value):
                    data[field_name] = value.mapped('name')
                else:
                    data[field_name] = [
                        _resolve_record_deep(r, depth - 1, _seen, _memo) for r in value
                    ]
    finally:
        _seen.discard(key)
    _memo[key] = data
    return data


def _record_summary(record):
    """Lightweight projection for ClassPicker dropdown entries."""
    return {
        'id': record.id,
        'name': getattr(record, 'name', None) or getattr(record, 'label', None) or str(record.id),
        'label': getattr(record, 'label', None) or getattr(record, 'name', None) or str(record.id),
        'description': (getattr(record, 'description', None) or '')[:240],
    }


def experiment_to_schema_dict(rec_id, depth=8):
    """Deep-resolve a stored experiment into a schema-shaped, JSON/YAML-ready dict.

    Cleans Odoo placeholders/metadata and restores schema slot names; the
    keyed-dict vs list shape is settled later by ``pydantic_loader`` (which
    coerces Odoo's many2many lists into the schema's keyed dicts). Returns
    ``None`` when the record does not exist.
    """
    rec = request.env['tvbo.simulation_experiment'].sudo().browse(rec_id)
    if not rec.exists():
        return None
    resolved = _clean(_resolve_record_deep(rec, depth=depth)) or {}
    data = _rename_reserved(_flatten_parent_links(resolved))

    # The current schema folds derived observations into `observations`
    # (Observation records carrying source_observations); the platform's Odoo
    # model still keeps a separate `derived_observations` m2m. Merge it back.
    derived = data.pop('derived_observations', None)
    if derived:
        derived = derived if isinstance(derived, list) else [derived]
        obs = data.get('observations')
        if isinstance(obs, list):
            obs.extend(derived)
        elif obs:
            data['observations'] = [obs] + derived
        else:
            data['observations'] = derived

    # `number_of_nodes` is only authoritative for a fully artificial network that
    # defines its size by count alone. Whenever the network carries a node source
    # — explicit `nodes`, or a connectome to resolve (`bids_dir` / `data_file` /
    # `parcellation` / `graph_generator` / `tractogram`) — the count is derivable,
    # and emitting the stored Odoo placeholder (e.g. 1) would misrepresent a
    # resolved connectome. Drop it in that case and let tvbo compute it on load.
    net = data.get('network')
    if isinstance(net, dict) and net.get('number_of_nodes') is not None:
        if any(net.get(k) for k in (
                'nodes', 'bids_dir', 'data_file', 'parcellation',
                'graph_generator', 'tractogram')):
            net.pop('number_of_nodes', None)

    return data


def validate_experiment(rec_id, depth=8):
    """Return ``(pydantic_obj, errors)`` for a stored experiment.

    ``(None, 'not_found')`` if missing, ``(None, [pydantic errors])`` if the
    stored data does not satisfy the schema, ``(obj, None)`` on success. Shared
    by the YAML download, the JSON ``/spec`` endpoint and anything else that
    needs a validated experiment.
    """
    from tvbo.utils import pydantic_loader
    from pydantic import ValidationError

    data = experiment_to_schema_dict(rec_id, depth=depth)
    if data is None:
        return None, 'not_found'
    try:
        # drop_unknown: ignore platform-only Odoo fields (e.g. portal
        # visibility/owner) that aren't part of the tvbo schema.
        obj = pydantic_loader.validate(data, 'SimulationExperiment', drop_unknown=True)
        return obj, None
    except ValidationError as ve:
        return None, ve.errors()


def validate_instance(class_name, rec_id, depth=6):
    """Validate any single building block (Dynamics, Network, Coupling, ...) by
    class + id, returning ``(pydantic_obj, errors)`` like :func:`validate_experiment`.
    Lets the Experiment Builder seed a new experiment from a Knowledge-Graph card."""
    from tvbo.utils import pydantic_loader
    from pydantic import ValidationError

    model_name = _class_to_odoo_model(class_name)
    if not model_name:
        return None, 'not_found'
    rec = request.env[model_name].sudo().browse(rec_id)
    if not rec.exists():
        return None, 'not_found'
    data = _rename_reserved(_flatten_parent_links(_clean(_resolve_record_deep(rec, depth=depth)) or {}))
    try:
        return pydantic_loader.validate(data, class_name, drop_unknown=True), None
    except ValidationError as ve:
        return None, ve.errors()


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
        type='jsonrpc', auth='user', methods=['POST'], csrf=False,
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
        type='jsonrpc', auth='public', methods=['POST'], csrf=False,
    )
    def api_experiment_serialize(self, **kwargs):
        """Validate assembled experiment JSON and return schema-correct YAML.

        This is the single source of truth for the builder's YAML download,
        "Copy" buttons and live preview. Validation goes through
        ``tvbo.utils.pydantic_loader`` (strict Pydantic, ``extra="forbid"``),
        which normalises TVBO's keyed-dict collections (``parameters: {a: ...}``
        -> ``name: a``) and strips file-envelope keys before validating. The
        emitted YAML is *bare* (``id`` at the top level), exactly the shape
        ``SimulationExperiment.from_file`` / ``from_string`` expect.

        Body: {
          "experiment": {...},                 # required
          "format": "yaml"|"json",             # default yaml
          "target_class": "SimulationExperiment"  # default; any tvbo class
        }
        """
        try:
            from tvbo.utils import pydantic_loader
            from pydantic import ValidationError

            payload = kwargs.get('experiment')
            if payload is None:
                return {'success': False, 'error': 'experiment is required'}
            if not isinstance(payload, dict):
                return {'success': False, 'error': 'experiment must be an object'}

            fmt = (kwargs.get('format') or 'yaml').lower()
            target = kwargs.get('target_class') or 'SimulationExperiment'

            try:
                obj = pydantic_loader.validate(payload, target)
            except ValidationError as ve:
                return {
                    'success': False,
                    'error': 'validation_error',
                    'errors': ve.errors(),
                }

            if fmt == 'json':
                return {
                    'success': True,
                    'format': 'json',
                    'data': obj.model_dump(mode='json', by_alias=True, exclude_none=True),
                }
            return {
                'success': True,
                'format': 'yaml',
                'yaml': pydantic_loader.dump(obj),
            }
        except ImportError as e:
            _logger.error('tvbo package missing: %s', e)
            return {'success': False, 'error': 'tvbo Python package not installed'}
        except Exception as e:
            _logger.error('serialize failed: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ---- 3b. Validated experiment spec (schema-shaped JSON) -----------------
    # The builder hydrates from this on load: a validated, schema-shaped dict
    # (keyed-dict collections, bare top level). The JS edits it in place and
    # POSTs it back to /serialize, so the client never has to reshape Odoo data.
    @http.route(
        '/tvbo/api/configurator/experiment/<int:rec_id>/spec',
        type='http', auth='public', methods=['GET'], csrf=False,
    )
    def api_experiment_spec(self, rec_id, **kwargs):
        try:
            obj, errors = validate_experiment(rec_id)
            if errors == 'not_found':
                return _json({'success': False, 'error': 'Not found'}, status=404)
            if errors:
                return _json({'success': False, 'error': 'validation_error', 'errors': errors})
            return _json({
                'success': True,
                'data': obj.model_dump(mode='json', by_alias=True, exclude_none=True),
            })
        except ImportError:
            return _json({'success': False, 'error': 'tvbo Python package not installed'}, status=500)
        except Exception as e:
            _logger.error('experiment spec failed: %s', e, exc_info=True)
            return _json({'success': False, 'error': str(e)}, status=500)

    # ---- 3c. Validated single building-block spec (schema-shaped JSON) ------
    # Lets the Experiment Builder seed a new experiment from a KG card
    # ("Open in Experiment Builder" on a Dynamics/Network/Coupling/... card).
    @http.route(
        '/tvbo/api/configurator/instances/<string:class_name>/<int:rec_id>/spec',
        type='http', auth='public', methods=['GET'], csrf=False,
    )
    def api_instance_spec(self, class_name, rec_id, **kwargs):
        try:
            obj, errors = validate_instance(class_name, rec_id)
            if errors == 'not_found':
                return _json({'success': False, 'error': 'Not found'}, status=404)
            if errors:
                return _json({'success': False, 'error': 'validation_error', 'errors': errors})
            return _json({
                'success': True,
                'class': class_name,
                'data': obj.model_dump(mode='json', by_alias=True, exclude_none=True),
            })
        except ImportError:
            return _json({'success': False, 'error': 'tvbo Python package not installed'}, status=500)
        except Exception as e:
            _logger.error('instance spec failed: %s', e, exc_info=True)
            return _json({'success': False, 'error': str(e)}, status=500)

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
            return request.make_response(
                yaml.dump(
                    data, default_flow_style=False,
                    sort_keys=False, allow_unicode=True,
                ),
                headers=[('Content-Type', 'application/x-yaml; charset=utf-8')],
            )
        except Exception as e:
            _logger.error('yaml_raw failed: %s', e, exc_info=True)
            return _json({'success': False, 'error': str(e)}, status=500)

    @http.route(
        '/tvbo/api/configurator/experiment/dump_yaml',
        type='jsonrpc', auth='public', methods=['POST'], csrf=False,
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
            return {
                'success': True,
                'yaml': yaml.dump(
                    data, default_flow_style=False,
                    sort_keys=False, allow_unicode=True,
                ),
            }
        except Exception as e:
            _logger.error('dump_yaml failed: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
