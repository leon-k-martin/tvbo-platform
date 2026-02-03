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
        """Get all networks"""
        try:
            records = request.env['tvbo.network'].sudo().search([])
            data = records.read()
            return self._json_response({'success': True, 'data': data})
        except Exception as e:
            _logger.error(f"Error in api_networks: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/configurator/monitors', type='http', auth='public', methods=['GET'], csrf=False)
    def api_monitors(self, **kwargs):
        """Get all monitors"""
        try:
            records = request.env['tvbo.monitor'].sudo().search([])
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
        """Export experiment as YAML using Pydantic SimulationExperiment model"""
        try:
            from tvbo.datamodel.tvbopydantic import SimulationExperiment
            import yaml

            exp = request.env['tvbo.simulation_experiment'].sudo().browse(experiment_id)
            if not exp.exists():
                return self._json_response({'success': False, 'error': 'Experiment not found'})

            # Convert Odoo record to Pydantic model
            pydantic_exp = self._odoo_to_pydantic(exp)

            # Export to YAML using Pydantic's model_dump
            data = pydantic_exp.model_dump(exclude_none=True, exclude_unset=True)
            yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

            return request.make_response(
                yaml_content,
                headers=[
                    ('Content-Type', 'text/yaml'),
                    ('Content-Disposition', f'attachment; filename="{exp.label or exp.name or "experiment"}.yaml"')
                ]
            )
        except ImportError as e:
            _logger.error(f"tvbo package not available: {e}")
            return self._json_response({'success': False, 'error': 'tvbo package not installed'})
        except Exception as e:
            _logger.error(f"Error in api_experiment_yaml: {e}", exc_info=True)
            return self._json_response({'success': False, 'error': str(e)})

    def _odoo_to_pydantic(self, odoo_record, pydantic_class=None):
        """
        Schema-driven conversion from Odoo record to Pydantic model.
        
        Design principle: Both Odoo and Pydantic models are generated from the same 
        LinkML schema, so field names match. No manual unpacking - iterate over 
        Pydantic model fields and pull corresponding values from Odoo.
        
        Raises on missing fields rather than silently skipping - we need to know
        when schema is out of sync.
        """
        from tvbo.datamodel import tvbopydantic as pyd
        from pydantic import BaseModel
        from odoo.fields import Many2one, Many2many
        
        if not odoo_record:
            return None
            
        # Infer Pydantic class from Odoo model name if not provided
        if pydantic_class is None:
            # tvbo.simulation_experiment -> SimulationExperiment
            model_name = odoo_record._name.replace('tvbo.', '')
            class_name = ''.join(word.capitalize() for word in model_name.split('_'))
            pydantic_class = getattr(pyd, class_name)
        
        # Build kwargs from Pydantic model fields
        kwargs = {}
        for field_name, field_info in pydantic_class.model_fields.items():
            # Skip internal fields
            if field_name in ('linkml_meta',):
                continue
                
            # Get value from Odoo record
            if not hasattr(odoo_record, field_name):
                continue  # Field not in Odoo model (e.g., computed field in Pydantic)
            
            odoo_value = getattr(odoo_record, field_name)
            odoo_field = odoo_record._fields.get(field_name)
            
            if odoo_value is False or odoo_value is None:
                # Odoo uses False for empty values
                kwargs[field_name] = None
                continue
            
            # Handle relation fields
            if odoo_field and isinstance(odoo_field, Many2one):
                # Recursively convert related record
                related_type = self._get_pydantic_type_from_annotation(field_info.annotation)
                if related_type and issubclass(related_type, BaseModel):
                    kwargs[field_name] = self._odoo_to_pydantic(odoo_value, related_type)
                else:
                    # Fallback: just get the ID or name
                    kwargs[field_name] = odoo_value.id if hasattr(odoo_value, 'id') else odoo_value
                    
            elif odoo_field and isinstance(odoo_field, Many2many):
                # Convert Many2many to dict (keyed by name) or list
                related_type = self._get_pydantic_type_from_annotation(field_info.annotation)
                if related_type and issubclass(related_type, BaseModel):
                    # Check if target is dict[str, X] or list[X]
                    origin = getattr(field_info.annotation, '__origin__', None)
                    if origin is dict:
                        kwargs[field_name] = {
                            rec.name: self._odoo_to_pydantic(rec, related_type)
                            for rec in odoo_value if hasattr(rec, 'name')
                        }
                    else:
                        kwargs[field_name] = [
                            self._odoo_to_pydantic(rec, related_type) for rec in odoo_value
                        ]
                else:
                    # Fallback: list of names or IDs
                    kwargs[field_name] = [rec.name if hasattr(rec, 'name') else rec.id for rec in odoo_value]
            else:
                # Simple field - direct assignment
                kwargs[field_name] = odoo_value
        
        return pydantic_class(**kwargs)
    
    def _get_pydantic_type_from_annotation(self, annotation):
        """Extract the base Pydantic model class from a type annotation."""
        from pydantic import BaseModel
        import typing
        
        # Handle Optional[X], dict[str, X], list[X], etc.
        origin = getattr(annotation, '__origin__', None)
        args = getattr(annotation, '__args__', ())
        
        if origin is type(None):
            return None
        elif origin in (dict, typing.Dict):
            # dict[str, X] -> return X
            if len(args) >= 2:
                return self._get_pydantic_type_from_annotation(args[1])
        elif origin in (list, typing.List):
            # list[X] -> return X
            if args:
                return self._get_pydantic_type_from_annotation(args[0])
        elif origin is typing.Union:
            # Optional[X] = Union[X, None] -> return X
            for arg in args:
                if arg is not type(None):
                    result = self._get_pydantic_type_from_annotation(arg)
                    if result:
                        return result
        elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation
        
        return None

    @http.route('/tvbo/configurator/save', type='jsonrpc', auth='user', website=True, csrf=True)
    def save_model(self, **kwargs):
        """Save a new neural mass model configuration to database"""
        try:
            data = kwargs.get('model_data')
            if not data:
                return {'success': False, 'error': 'No model data provided'}

            _logger.info(f"Saving model: {data.get('name')}")

            # Create the neural mass model
            model_vals = {
                'name': data.get('name'),
                'label': data.get('label') or data.get('name'),
                'description': data.get('description', ''),
                'number_of_modes': data.get('number_of_modes', 1),
            }

            # First create the Dynamics record (since NeuralMassModel inherits from it)
            dynamics = request.env['tvbo.dynamics'].sudo().create(model_vals)

            # Create parameters
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

            # Update the dynamics record with all relationships
            dynamics.write({
                'parameters': [(6, 0, param_ids)],
                'state_variables': [(6, 0, sv_ids)],
                'derived_variables': [(6, 0, dv_ids)],
                'coupling_terms': [(6, 0, ct_ids)],
            })

            return {
                'success': True,
                'model_id': dynamics.id,
                'message': f'Model "{data.get("name")}" created successfully!'
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
