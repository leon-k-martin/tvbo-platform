# -*- coding: utf-8 -*-
"""Authenticated REST API for the tvbo Python client.

Bearer-token auth using personal API keys (minted at /my/api-keys). Lets a user
read and push their saved + shared models (Dynamics) and SimulationExperiments
from Python.

    GET  /api/tvbo/v1/models                 list accessible models
    GET  /api/tvbo/v1/models/<id>            one model  (?format=yaml|json, default yaml)
    POST /api/tvbo/v1/models                 push a model (YAML or JSON body)
    GET  /api/tvbo/v1/experiments            list accessible experiments
    GET  /api/tvbo/v1/experiments/<id>       one experiment (?format=yaml|json)
    POST /api/tvbo/v1/experiments            push an experiment

Access mirrors the portal: ground-truth records (no share row) are public;
user-saved records are visible to their owner and, when shared, to everyone.
Enforced here in the controller (the schema entities stay field-free).
"""
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _auth_user():
    """Resolve the user from an ``Authorization: Bearer <key>`` header, or None."""
    auth = request.httprequest.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    user = request.env['tvbo.api_key'].sudo().verify(auth[7:].strip())
    return user or None


class TVBOApi(http.Controller):

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _resp(self, data, status=200):
        return request.make_response(
            json.dumps(data, default=str),
            headers=[('Content-Type', 'application/json')], status=status)

    def _yaml(self, text, filename):
        return request.make_response(text, headers=[
            ('Content-Type', 'application/x-yaml; charset=utf-8'),
            ('Content-Disposition', f'attachment; filename="{filename}.yaml"'),
        ])

    def _unauthorized(self):
        return self._resp(
            {'error': 'unauthorized', 'detail': 'Provide a valid Bearer API key.'},
            status=401)

    def _shares(self):
        return request.env['tvbo.model_share'].sudo()

    def _can_read(self, field, rec_id, user):
        """True if the record is public (no share), owned by user, or shared."""
        share = self._shares().search([(field, '=', rec_id)], limit=1)
        if not share:
            return True  # ground-truth / public
        return share.owner_user_id.id == user.id or share.visibility == 'shared'

    # ------------------------------------------------------------------ #
    # Models
    # ------------------------------------------------------------------ #
    @http.route('/api/tvbo/v1/models', type='http', auth='public',
                methods=['GET', 'POST'], csrf=False)
    def models(self, **kw):
        user = _auth_user()
        if not user:
            return self._unauthorized()
        if request.httprequest.method == 'POST':
            return self._push('Dynamics', 'tvbo.dynamics', 'dynamics_id', user)
        shares = self._shares().search(
            ['&', ('dynamics_id', '!=', False),
             '|', ('owner_user_id', '=', user.id), ('visibility', '=', 'shared')])
        items = [{
            'id': s.dynamics_id.id,
            'name': s.dynamics_id.name,
            'label': s.dynamics_id.label,
            'description': s.dynamics_id.description,
            'visibility': s.visibility,
            'owner': s.owner_user_id.name,
            'mine': s.owner_user_id.id == user.id,
        } for s in shares]
        return self._resp({'data': items})

    @http.route('/api/tvbo/v1/models/<int:model_id>', type='http', auth='public',
                methods=['GET'], csrf=False)
    def model_detail(self, model_id, format='yaml', **kw):
        user = _auth_user()
        if not user:
            return self._unauthorized()
        if not self._can_read('dynamics_id', model_id, user):
            return self._resp({'error': 'not_found'}, status=404)
        from .building_blocks_api import validate_instance
        obj, errors = validate_instance('Dynamics', model_id)
        if errors == 'not_found':
            return self._resp({'error': 'not_found'}, status=404)
        return self._serialized(obj, errors, format, f'model_{model_id}')

    # ------------------------------------------------------------------ #
    # Experiments
    # ------------------------------------------------------------------ #
    @http.route('/api/tvbo/v1/experiments', type='http', auth='public',
                methods=['GET', 'POST'], csrf=False)
    def experiments(self, **kw):
        user = _auth_user()
        if not user:
            return self._unauthorized()
        if request.httprequest.method == 'POST':
            return self._push('SimulationExperiment', 'tvbo.simulation_experiment',
                              'experiment_id', user)
        # Experiments others marked private are excluded; everything else (public
        # ground-truth, own, shared) is listed.
        private_ids = self._shares().search(
            [('experiment_id', '!=', False), ('visibility', '=', 'private'),
             ('owner_user_id', '!=', user.id)]).mapped('experiment_id').ids
        exps = request.env['tvbo.simulation_experiment'].sudo().search(
            [('id', 'not in', private_ids)] if private_ids else [])
        # Experiments are identified by ``label`` (the model has no ``name`` field).
        items = [{
            'id': e.id, 'label': e.label, 'description': e.description,
        } for e in exps]
        return self._resp({'data': items})

    @http.route('/api/tvbo/v1/experiments/<int:experiment_id>', type='http',
                auth='public', methods=['GET'], csrf=False)
    def experiment_detail(self, experiment_id, format='yaml', **kw):
        user = _auth_user()
        if not user:
            return self._unauthorized()
        if not self._can_read('experiment_id', experiment_id, user):
            return self._resp({'error': 'not_found'}, status=404)
        from .building_blocks_api import validate_experiment
        obj, errors = validate_experiment(experiment_id)
        if errors == 'not_found':
            return self._resp({'error': 'not_found'}, status=404)
        return self._serialized(obj, errors, format, f'experiment_{experiment_id}')

    def _serialized(self, obj, errors, fmt, filename):
        from tvbo.utils import pydantic_loader
        if errors:
            return self._resp({'error': 'validation_error', 'errors': errors}, status=422)
        if fmt == 'json':
            return self._resp(
                {'data': obj.model_dump(mode='json', by_alias=True, exclude_none=True)})
        return self._yaml(pydantic_loader.dump(obj), filename)

    # ------------------------------------------------------------------ #
    # Push (save from Python)
    # ------------------------------------------------------------------ #
    def _push(self, class_name, model_name, share_field, user):
        from tvbo.utils import pydantic_loader
        from ..models.ingest import _create_record

        raw = request.httprequest.get_data(as_text=True) or ''
        ctype = request.httprequest.content_type or ''
        # Visibility from ?visibility= applies to both YAML and JSON pushes; a
        # JSON body's own "visibility" still overrides it below.
        qs_vis = request.httprequest.args.get('visibility')
        visibility = qs_vis if qs_vis in ('private', 'shared') else 'private'
        try:
            if 'json' in ctype:
                payload = json.loads(raw) if raw else {}
                if isinstance(payload, dict) and payload.get('visibility') in ('private', 'shared'):
                    visibility = payload['visibility']
                if isinstance(payload, dict) and 'yaml' in payload:
                    obj = pydantic_loader.loads(payload['yaml'], class_name)
                else:
                    spec = payload.get('spec', payload) if isinstance(payload, dict) else payload
                    obj = pydantic_loader.validate(spec, class_name, drop_unknown=True)
            else:
                obj = pydantic_loader.loads(raw, class_name)
        except Exception as exc:  # noqa: BLE001
            return self._resp({'error': 'validation_error', 'detail': str(exc)}, status=422)

        data = obj.model_dump(mode='python', by_alias=True, exclude_none=True)
        name = data.get('name') or data.get('label')

        # Replace-on-name: if the user already owns an element of this kind with
        # the same identifier, drop it first so pushes update in place. Compare on
        # each target's own ``_rec_name`` (``name`` for models, ``label`` for
        # experiments) so this works for both kinds.
        owned = self._shares().search(
            [(share_field, '!=', False), ('owner_user_id', '=', user.id)])
        if name:
            stale = owned.filtered(
                lambda s: s.target[s.target._rec_name] == name)
            stale.purge_model()

        rec_id = _create_record(request.env, model_name, data, {})
        if not rec_id:
            return self._resp({'error': 'create_failed'}, status=500)
        self._shares().create({
            share_field: rec_id, 'owner_user_id': user.id, 'visibility': visibility})
        return self._resp(
            {'success': True, 'id': rec_id, 'name': name, 'visibility': visibility},
            status=201)
