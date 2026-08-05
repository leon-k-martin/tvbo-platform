# -*- coding: utf-8 -*-
import logging
import requests
from odoo import http
from odoo.http import request

from .assets import json_payload

_logger = logging.getLogger(__name__)

MINERU_API_URL = 'http://mineru:8000'


class DocumentParserController(http.Controller):

    @http.route('/tvbo/parser', type='http', auth='public', website=True)
    def parser_page(self, **kwargs):
        return request.render('tvbo.document_parser_template', {})

    @http.route('/tvbo/api/parse', type='http', auth='public', methods=['POST'], csrf=False)
    def parse_document(self, **kwargs):
        """Proxy upload to MinerU API and return Markdown result."""
        uploaded = request.httprequest.files.get('file')
        if not uploaded:
            return self._json_response({'success': False, 'error': 'No file uploaded'})

        try:
            resp = requests.post(
                f'{MINERU_API_URL}/file_parse',
                files={'files': (uploaded.filename, uploaded.stream, uploaded.content_type)},
                data={'return_md': 'true'},
                timeout=300,
            )
            resp.raise_for_status()
            result = resp.json()
            return self._json_response({'success': True, 'data': result})
        except requests.ConnectionError:
            return self._json_response({'success': False, 'error': 'MinerU service unavailable'})
        except Exception as e:
            _logger.exception('Document parsing failed')
            return self._json_response({'success': False, 'error': str(e)})

    @http.route('/tvbo/api/parse/health', type='http', auth='public', methods=['GET'], csrf=False)
    def parse_health(self, **kwargs):
        """Check MinerU service health."""
        try:
            resp = requests.get(f'{MINERU_API_URL}/health', timeout=5)
            return self._json_response({'success': True, 'data': resp.json()})
        except Exception:
            return self._json_response({'success': False, 'error': 'MinerU service unavailable'})

    def _json_response(self, data):
        return json_payload(data)
