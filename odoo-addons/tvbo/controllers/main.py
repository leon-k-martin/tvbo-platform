# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request


class TVBOWebsite(http.Controller):

    @http.route('/', type='http', auth='public', website=True)
    def index(self, **kw):
        """TVBO Database homepage."""
        return request.render('tvbo.tvbo_homepage_view', {})

    @http.route('/tvbo/models', type='http', auth='public', website=True)
    def models(self, **kw):
        """List neural models: the public ground-truth DB plus shared user models.

        Private user-saved models are excluded so they never leak into the
        public gallery — their owner finds them under /my/models instead.
        """
        private_ids = request.env['tvbo.model_share'].sudo().search(
            [('visibility', '=', 'private')]).mapped('dynamics_id').ids
        domain = [('id', 'not in', private_ids)] if private_ids else []
        models = request.env['tvbo.dynamics'].sudo().search(domain)
        return request.render('tvbo.tvbo_models_list', {
            'models': models,
        })

    @http.route('/tvbo/model/<int:model_id>', type='http', auth='public', website=True)
    def model_detail(self, model_id, **kw):
        """Show detailed neural model information.

        A user's private model is viewable only by its owner; ground-truth and
        shared models are public.
        """
        model = request.env['tvbo.dynamics'].sudo().browse(model_id)
        if not model.exists():
            return request.not_found()
        share = request.env['tvbo.model_share'].sudo().search(
            [('dynamics_id', '=', model_id)], limit=1)
        if (share and share.visibility != 'shared'
                and share.owner_user_id.id != request.env.user.id):
            return request.not_found()
        return request.render('tvbo.tvbo_model_detail', {
            'model': model,
            'share': share,
        })

    @http.route('/tvbo/integrators', type='http', auth='public', website=True)
    def integrators(self, **kw):
        """List all integrators."""
        integrators = request.env['tvbo.integrator'].sudo().search([])
        return request.render('tvbo.tvbo_integrators_list', {
            'integrators': integrators,
        })

    @http.route('/tvbo/networks', type='http', auth='public', website=True)
    def networks(self, **kw):
        """List all connectivity networks."""
        networks = request.env['tvbo.network'].sudo().search([])
        return request.render('tvbo.tvbo_networks_list', {
            'networks': networks,
        })

    @http.route('/tvbo/studies', type='http', auth='public', website=True)
    def studies(self, **kw):
        """List all research studies."""
        studies = request.env['tvbo.simulation_experiment'].sudo().search([])
        return request.render('tvbo.tvbo_studies_list', {
            'studies': studies,
        })

    @http.route('/tvbo/kg', type='http', auth='public', website=True)
    def knowledge_graph(self, **kw):
        """Knowledge Graph Browser - API-powered search interface."""
        return request.render('tvbo.tvbo_kg_browser', {})

    @http.route('/tvbo/agents', type='http', auth='public', website=True)
    def agentic_coding(self, **kw):
        """Agentic Coding with TVBO — high-level intro for all user groups."""
        return request.render('tvbo.tvbo_agents_page', {})
