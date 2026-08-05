# -*- coding: utf-8 -*-
from odoo import models

from ..compression import compress_response


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _post_dispatch(cls, response):
        """Gzip every dispatched response — see :mod:`..compression`.

        This is the last hook Odoo runs before the response goes to WSGI, so it
        covers website HTML, the ``/web/assets`` bundles and the JSON APIs in one
        place. Static files never reach it; ``/tvbo/z/`` handles those.
        """
        super()._post_dispatch(response)
        compress_response(response)
