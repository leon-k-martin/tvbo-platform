# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class ModelConfiguratorController(http.Controller):

    @http.route('/tvbo/configurator', type='http', auth='public', website=True)
    def model_configurator(self, **kwargs):
        """Main configurator page - data is loaded via API endpoints"""
        return request.render('tvbo.model_configurator_template', {})

    # =========================================================================
    # Generic API Endpoints for Configurator Data
    # =========================================================================

    def _json_response(self, data):
        """Helper to create JSON response"""
        return request.make_response(
            json.dumps(data, default=str),
            headers=[('Content-Type', 'application/json')]
        )

    def _serialize_records(self, records, fields=None):
        """Generic serializer using Odoo's read() method"""
        if not records:
            return []
        if fields:
            return records.read(fields)
        # Default: read all fields
        return records.read()

    @http.route('/tvbo/api/configurator/experiments', type='http', auth='public', methods=['GET'], csrf=False)
    def api_experiments(self, **kwargs):
        """Get all simulation experiments"""
        try:
            records = request.env['tvbo.simulation_experiment'].sudo().search([])
            data = records.read()
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_experiments: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/dynamics', type='http', auth='public', methods=['GET'], csrf=False)
    def api_dynamics(self, **kwargs):
        """Get all dynamics models"""
        try:
            records = request.env['tvbo.dynamics'].sudo().search([])
            data = records.read()
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_dynamics: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/dynamics/<int:dynamics_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def api_dynamics_detail(self, dynamics_id, **kwargs):
        """
        Get full details of a dynamics model with all nested relations resolved.
        
        Schema-driven: Uses _resolve_record_deep to automatically resolve
        all Many2one/Many2many relations without manual field unpacking.
        """
        try:
            dyn = request.env['tvbo.dynamics'].sudo().browse(dynamics_id)
            if not dyn.exists():
                return self._json_response({'success': False, 'error': 'Not found'})
            
            # Schema-driven deep resolution - no manual unpacking
            data = self._resolve_record_deep(dyn, depth=3)
            
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_dynamics_detail: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/integrators', type='http', auth='public', methods=['GET'], csrf=False)
    def api_integrators(self, **kwargs):
        """Get all integrators"""
        try:
            records = request.env['tvbo.integrator'].sudo().search([])
            data = records.read()
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_integrators: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/couplings', type='http', auth='public', methods=['GET'], csrf=False)
    def api_couplings(self, **kwargs):
        """Get all coupling functions"""
        try:
            records = request.env['tvbo.coupling'].sudo().search([])
            data = records.read()
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_couplings: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/networks', type='http', auth='public', methods=['GET'], csrf=False)
    def api_networks(self, **kwargs):
        """Get all networks plus the tractograms / parcellations available
        as Many2one targets (used to populate the Network panel selectors)."""
        try:
            records = request.env['tvbo.network'].sudo().search([])
            data = records.read()

            tractograms = request.env['tvbo.tractogram'].sudo().search([]).read(
                ['id', 'name', 'label', 'description'])
            parcellations = request.env['tvbo.parcellation'].sudo().search([]).read(
                ['id', 'label', 'atlas'])

            return self._json_response({
                'success': True,
                'data': data,
                'tractograms': tractograms,
                'parcellations': parcellations,
            })
        except Exception as e:
            _logger.error(f"Error in api_networks: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/monitors', type='http', auth='public', methods=['GET'], csrf=False)
    def api_monitors(self, **kwargs):
        """Get all monitors. The schema folds monitors into Observation, so this
        serves tvbo.observation records (kept under the /monitors path for the
        existing frontend)."""
        try:
            records = request.env['tvbo.observation'].sudo().search([])
            data = records.read()
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_monitors: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/experiment/<int:experiment_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def api_experiment_detail(self, experiment_id, **kwargs):
        """
        Get full experiment details with all nested relations resolved.
        
        Schema-driven: Uses _resolve_record_deep to automatically resolve
        all Many2one/Many2many relations without manual field unpacking.
        """
        try:
            exp = request.env['tvbo.simulation_experiment'].sudo().browse(experiment_id)
            if not exp.exists():
                return self._json_response({'success': False, 'error': 'Experiment not found'})

            # Schema-driven deep resolution - no manual unpacking
            data = self._resolve_record_deep(exp, depth=4)
            
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_experiment_detail: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    def _resolve_record_deep(self, record, depth=3):
        """
        Schema-driven deep resolution of Odoo record with all relations.
        
        Design principle: Trust the schema completely. Iterate over all fields
        in the record and resolve Many2one/Many2many relations automatically.
        No manual field-by-field unpacking - if schema changes, this adapts.
        
        Args:
            record: Odoo record to resolve
            depth: Maximum recursion depth to prevent infinite loops (default 3)
        
        Returns:
            dict with all fields resolved, relations expanded to full data
        """
        if not record or depth <= 0:
            return None
        
        data = record.read()[0]
        
        # Iterate over all fields in the model - schema-driven, no manual unpacking
        for field_name, field_obj in record._fields.items():
            # Skip internal/system fields
            if field_name in ('id', 'display_name', 'create_uid', 'create_date', 
                              'write_uid', 'write_date', '__last_update'):
                continue
            
            field_value = getattr(record, field_name, None)
            
            # Skip empty values (Odoo uses False for empty)
            if not field_value:
                continue
            
            # Resolve Many2one - single related record
            if field_obj.type == 'many2one':
                data[field_name] = self._resolve_record_deep(field_value, depth - 1)
            
            # Resolve Many2many/One2many - collection of related records
            elif field_obj.type in ('many2many', 'one2many'):
                data[field_name] = [
                    self._resolve_record_deep(r, depth - 1) for r in field_value
                ]
        
        return data

    @http.route('/tvbo/api/configurator/experiment/<int:experiment_id>/yaml', type='http', auth='public', methods=['GET'], csrf=False)
    def api_experiment_yaml(self, experiment_id, **kwargs):
        """Export a stored experiment as schema-valid, bare TVBO YAML.

        Deep-resolves the Odoo record, cleans Odoo placeholders/metadata and
        restores schema slot names, then validates + serialises through
        ``tvbo.utils.pydantic_loader`` (which coerces Odoo's many2many lists into
        the schema's keyed-dict collections). The output is exactly what
        ``SimulationExperiment.from_file`` expects.
        """
        try:
            import re
            import unicodedata
            from tvbo.utils import pydantic_loader
            from .building_blocks_api import validate_experiment

            exp = request.env['tvbo.simulation_experiment'].sudo().browse(experiment_id)
            if not exp.exists():
                return self._json_response({'success': False, 'error': 'Experiment not found'})

            obj, errors = validate_experiment(experiment_id)
            if errors:
                _logger.warning("experiment %s failed schema validation: %s", experiment_id, errors)
                return self._json_response({
                    'success': False, 'error': 'validation_error', 'errors': errors,
                })

            yaml_content = pydantic_loader.dump(obj)
            # ASCII-safe filename: HTTP headers are Latin-1, and labels can contain
            # non-ASCII characters (e.g. em-dashes, Greek letters in bifurcation
            # experiments), which would break the Content-Disposition header.
            raw_name = exp.label or exp.name or 'experiment'
            ascii_name = unicodedata.normalize('NFKD', raw_name).encode('ascii', 'ignore').decode('ascii')
            filename = re.sub(r'[^\w.-]+', '_', ascii_name).strip('_') or 'experiment'
            return request.make_response(
                yaml_content,
                headers=[
                    ('Content-Type', 'application/x-yaml; charset=utf-8'),
                    ('Content-Disposition', f'attachment; filename="{filename}.yaml"'),
                ]
            )
        except ImportError as e:
            _logger.error(f"tvbo package not available: {e}")
            return self._json_response({'success': False, 'error': 'tvbo package not installed'})
        except Exception as e:
            _logger.error(f"Error in api_experiment_yaml: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/experiment/<int:experiment_id>/bundle', type='http', auth='public', methods=['GET'], csrf=False)
    def api_experiment_bundle(self, experiment_id, **kwargs):
        """Download a self-contained experiment bundle: one monolithic YAML plus
        the network connectome as an HDF5 companion (+ sidecar), zipped.

        The bundled YAML references the connectome via ``network.data_file`` so it
        loads standalone with ``SimulationExperiment.from_file`` — no external BIDS
        directory needed. Experiments without a multi-node network (e.g. single-node
        bifurcation studies) bundle to just the YAML. ``label``/``description`` query
        params override the corresponding fields (so builder edits carry through).
        """
        import json as _json

        def _err(status, payload):
            # Binary-download route: signal failure with a real HTTP status so the
            # client can distinguish it from a valid ZIP (never a 200 JSON body).
            return request.make_response(_json.dumps(payload), status=status,
                                         headers=[('Content-Type', 'application/json')])
        try:
            import io
            import os
            import re
            import shutil
            import tempfile
            import unicodedata
            import zipfile
            from pathlib import Path
            import yaml as _yaml
            import tvbo
            from tvbo.utils import pydantic_loader
            from tvbo.classes.experiment import SimulationExperiment
            from tvbo.classes.network import Network
            from .building_blocks_api import validate_experiment

            exp_rec = request.env['tvbo.simulation_experiment'].sudo().browse(experiment_id)
            if not exp_rec.exists():
                return _err(404, {'success': False, 'error': 'Experiment not found'})

            # Respect model-sharing visibility: a private experiment is downloadable
            # only by its owner. Curated experiments have no share row -> public.
            share = request.env['tvbo.model_share'].sudo().search(
                [('experiment_id', '=', experiment_id)], limit=1)
            if share and share.visibility == 'private':
                user = request.env.user
                if user._is_public() or share.owner_user_id.id != user.id:
                    return _err(403, {'success': False, 'error': 'forbidden'})

            obj, errors = validate_experiment(experiment_id)
            if errors:
                return _err(422, {'success': False, 'error': 'validation_error', 'errors': errors})

            spec = _yaml.safe_load(pydantic_loader.dump(obj))
            for k in ('label', 'description'):  # not 'name' — schema identifier slot
                if kwargs.get(k):
                    spec[k] = kwargs[k]
            # References edited in the builder (one per line). Only override when the
            # existing value is absent or a plain list of citekey strings, so we never
            # clobber object-shaped reference entries the schema may require.
            refs = (kwargs.get('references') or '').strip()
            if refs:
                cur = spec.get('references')
                if cur is None or (isinstance(cur, list) and all(isinstance(x, str) for x in cur)):
                    spec['references'] = [r.strip() for r in refs.splitlines() if r.strip()]

            tmp = tempfile.mkdtemp(prefix='tvbo_bundle_')
            try:
                # Resolve a relative bids_dir against tvbo's experiments dir so the
                # connectome resolves regardless of the temp file's location.
                db_exp = Path(tvbo.__file__).resolve().parent / 'database' / 'experiments'
                net_spec = spec.get('network')
                if isinstance(net_spec, dict) and net_spec.get('bids_dir') and not os.path.isabs(net_spec['bids_dir']):
                    net_spec['bids_dir'] = str((db_exp / net_spec['bids_dir']).resolve())

                exp_path = os.path.join(tmp, 'experiment.yaml')
                with open(exp_path, 'w') as fh:
                    _yaml.safe_dump(spec, fh, sort_keys=False, allow_unicode=True)

                experiment = SimulationExperiment.from_file(exp_path)
                files = ['experiment.yaml']
                if isinstance(net_spec, dict) and (getattr(experiment.network, 'number_of_nodes', 0) or 0) > 1:
                    n = experiment.network
                    if not isinstance(n, Network):
                        n.__class__ = Network
                    if getattr(n, 'bids_dir', None):
                        try:
                            n.bids_dir = None
                        except Exception:  # noqa: BLE001
                            object.__setattr__(n, 'bids_dir', None)
                    n.save(os.path.join(tmp, 'connectome.yaml'), binary_format='h5')
                    # Load weights from the HDF5 companion, but KEEP the inline network
                    # (normalization transforms, coupling, parameters). Collapsing the
                    # network to {label, data_file} drops the `W / W_max` transform, so
                    # the standalone run gets raw weights and diverges to all-NaN.
                    net_block = {k: v for k, v in net_spec.items() if k != 'bids_dir'}
                    net_block['data_file'] = 'connectome.h5'
                    transforms = net_block.get('transforms') or []
                    if not any(isinstance(t, dict) and t.get('name') == 'weight' for t in transforms):
                        net_block['transforms'] = list(transforms) + [
                            {'name': 'weight', 'equation': {'rhs': 'W / W_max'}}]
                    spec['network'] = net_block
                    with open(exp_path, 'w') as fh:
                        _yaml.safe_dump(spec, fh, sort_keys=False, allow_unicode=True)
                    files += ['connectome.yaml', 'connectome.h5']

                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
                    for fn in files:
                        p = os.path.join(tmp, fn)
                        if os.path.exists(p):
                            z.write(p, fn)
                data = buf.getvalue()
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

            ascii_name = unicodedata.normalize('NFKD', exp_rec.label or 'experiment').encode('ascii', 'ignore').decode('ascii')
            filename = re.sub(r'[^\w.-]+', '_', ascii_name).strip('_') or 'experiment'
            return request.make_response(data, headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', f'attachment; filename="{filename}_bundle.zip"'),
            ])
        except ImportError as e:
            _logger.error(f"tvbo package not available: {e}")
            return _err(500, {'success': False, 'error': 'tvbo package not installed'})
        except Exception as e:  # noqa: BLE001
            _logger.error(f"Error in api_experiment_bundle: {e}", exc_info=True)
            return _err(500, {'success': False, 'error': str(e)})

    @http.route('/tvbo/configurator/save', type='jsonrpc', auth='user', website=True, csrf=True)
    def save_model(self, **kwargs):
        """Save a new neural mass model configuration to database"""
        try:
            data = kwargs.get('model_data')
            if not data:
                return {'success': False, 'error': 'No model data provided'}

            _logger.info(f"Saving model: {data.get('name')}")

            # request.env.user is the real session user even though we create
            # with sudo() below — capture it before sudo to stamp ownership.
            owner_id = request.env.user.id

            # Create the neural mass model
            model_vals = {
                'name': data.get('name'),
                'label': data.get('label') or data.get('name'),
                'description': data.get('description', ''),
                'number_of_modes': data.get('number_of_modes', 1),
            }

            # Build the child records first — independent of whether we end up
            # creating a new model or updating one the user already owns.
            param_ids = []
            for param_data in data.get('parameters', []):
                # Create domain (Range) if provided
                domain_id = None
                if param_data.get('domain'):
                    domain_vals = {
                        'lo': param_data['domain'].get('lo'),
                        'hi': param_data['domain'].get('hi'),
                        'step': param_data['domain'].get('step'),
                    }
                    domain = request.env['tvbo.range'].sudo().create(domain_vals)
                    domain_id = domain.id

                param_vals = {
                    'name': param_data.get('name'),
                    'value': param_data.get('value'),
                    'unit': param_data.get('unit'),
                    'description': param_data.get('description'),
                    'domain': domain_id,
                }
                param = request.env['tvbo.parameter'].sudo().create(param_vals)
                param_ids.append(param.id)

            # Create state variables
            sv_ids = []
            for sv_data in data.get('state_variables', []):
                # Create equation if provided
                eq_id = None
                if sv_data.get('equation'):
                    eq_vals = {
                        'lefthandside': sv_data['equation'].get('lhs'),
                        'righthandside': sv_data['equation'].get('rhs'),
                    }
                    equation = request.env['tvbo.equation'].sudo().create(eq_vals)
                    eq_id = equation.id

                # Create domain if provided
                domain_id = None
                if sv_data.get('domain'):
                    domain_vals = {
                        'lo': sv_data['domain'].get('lo'),
                        'hi': sv_data['domain'].get('hi'),
                    }
                    domain = request.env['tvbo.range'].sudo().create(domain_vals)
                    domain_id = domain.id

                sv_vals = {
                    'name': sv_data.get('name'),
                    'description': sv_data.get('description'),
                    'initial_value': sv_data.get('initial_value', 0.1),
                    'equation': eq_id,
                    'domain': domain_id,
                }
                sv = request.env['tvbo.state_variable'].sudo().create(sv_vals)
                sv_ids.append(sv.id)

            # Create derived variables
            dv_ids = []
            for dv_data in data.get('derived_variables', []):
                eq_id = None
                if dv_data.get('equation'):
                    eq_vals = {
                        'lefthandside': dv_data['equation'].get('lhs'),
                        'righthandside': dv_data['equation'].get('rhs'),
                    }
                    equation = request.env['tvbo.equation'].sudo().create(eq_vals)
                    eq_id = equation.id

                dv_vals = {
                    'name': dv_data.get('name'),
                    'description': dv_data.get('description'),
                    'equation': eq_id,
                }
                dv = request.env['tvbo.derived_variable'].sudo().create(dv_vals)
                dv_ids.append(dv.id)

            # Create coupling terms
            ct_ids = []
            for ct_data in data.get('coupling_terms', []):
                ct_vals = {
                    'name': ct_data.get('name'),
                    'value': ct_data.get('value'),
                }
                ct = request.env['tvbo.parameter'].sudo().create(ct_vals)
                ct_ids.append(ct.id)

            relations = {
                'parameters': [(6, 0, param_ids)],
                'state_variables': [(6, 0, sv_ids)],
                'derived_variables': [(6, 0, dv_ids)],
                'coupling_terms': [(6, 0, ct_ids)],
            }

            Dynamics = request.env['tvbo.dynamics'].sudo()
            Share = request.env['tvbo.model_share'].sudo()

            # Update-in-place: if the user already owns a model with this name,
            # update it instead of creating a duplicate (and drop the children it
            # previously owned so they don't pile up as orphans).
            owned = Share.search([('owner_user_id', '=', owner_id)]).dynamics_id
            existing = owned.filtered(lambda d: d.name == model_vals['name'])[:1]

            if existing:
                dynamics = existing
                stale_children = dynamics._saved_model_children()
                dynamics.write({**model_vals, **relations})
                dynamics._unlink_saved_children(stale_children)
                action = 'updated'
            else:
                dynamics = Dynamics.create(model_vals)
                dynamics.write(relations)
                # Platform-only ownership/sharing record (kept off tvbo.dynamics
                # so it never leaks into the schema-validated serialization).
                Share.create({
                    'dynamics_id': dynamics.id,
                    'owner_user_id': owner_id,
                    'visibility': 'private',
                })
                action = 'saved'

            return {
                'success': True,
                'model_id': dynamics.id,
                'view_url': f'/tvbo/model/{dynamics.id}',
                'manage_url': '/my/models',
                'message': f'Model "{data.get("name")}" {action} to your account!'
            }

        except Exception as e:
            _logger.error(f"Error saving model: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/tvbo/configurator/run', type='jsonrpc', auth='public', website=True, csrf=False)
    def run_simulation(self, **kwargs):
        """
        Run a simulation experiment by proxying to the TVBO API container.
        """
        import requests
        import os

        try:
            experiment_data = kwargs.get('experiment')
            duration = kwargs.get('duration')
            step_size = kwargs.get('step_size')
            backend = kwargs.get('backend')

            # MVP: Fail explicitly if required params missing
            if not experiment_data:
                return {'success': False, 'error': 'No experiment data provided'}
            if duration is None:
                return {'success': False, 'error': 'duration is required'}
            if step_size is None:
                return {'success': False, 'error': 'step_size is required'}
            if not backend:
                return {'success': False, 'error': 'backend is required'}

            _logger.info(f"Running simulation: duration={duration}ms, step_size={step_size}ms, backend={backend}")
            _logger.info(f"Experiment data: {experiment_data}")

            # Build the request payload for TVBO API
            payload = {
                'experiment': experiment_data,
                'duration': float(duration),
                'step_size': float(step_size),
                'backend': backend,
            }

            # Call the TVBO API container
            tvbo_api_url = os.environ.get('TVBO_API_URL', 'http://tvbo-api:8000')
            _logger.info(f"Calling TVBO API at {tvbo_api_url}/experiment/run")

            response = requests.post(
                f'{tvbo_api_url}/experiment/run',
                json=payload,
                timeout=300
            )

            _logger.info(f"TVBO API response status: {response.status_code}")
            result = response.json()
            _logger.info(f"TVBO API response keys: {list(result.keys())}")
            _logger.info(f"TVBO API success: {result.get('success')}")

            if response.status_code != 200:
                error_msg = result.get('detail', response.text)
                _logger.error(f"TVBO API error: {error_msg}")
                return {'success': False, 'error': f'TVBO API error: {error_msg}'}

            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error from TVBO API')
                _logger.error(f"TVBO API returned failure: {error_msg}")
                return {'success': False, 'error': error_msg}

            # MVP: No fallbacks - pass through exactly what API returns
            _logger.info(f"Returning data with {len(result.get('data', []))} time points")
            return {
                'success': True,
                'data': result.get('data'),
                'time': result.get('time'),
                'state_variables': result.get('state_variables'),
                'region_labels': result.get('region_labels'),
                'sample_period': result.get('sample_period'),
                'message': 'Simulation completed successfully'
            }

        except requests.exceptions.ConnectionError:
            _logger.error("Cannot connect to TVBO API container")
            return {
                'success': False,
                'error': 'Cannot connect to TVBO API. Please ensure the tvbo-api container is running.'
            }
        except requests.exceptions.Timeout:
            _logger.error("TVBO API request timed out")
            return {
                'success': False,
                'error': 'Simulation timed out. Try reducing the duration or increasing step size.'
            }
        except Exception as e:
            _logger.error(f"Error running simulation: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
