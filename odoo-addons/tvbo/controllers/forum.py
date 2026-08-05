# -*- coding: utf-8 -*-
"""Forum entry points: a friendly signed-out /ask, and the topic-type field.

Odoo routes ``/forum/<forum>/ask`` with ``auth="user"``. When an anonymous
visitor opens it, Odoo raises ``SessionExpiredException`` and its handler builds
the /web/login redirect through ``request.env['ir.http']`` — but ``request.env``
is already gone at that point, so the visitor gets a raw 500 instead of a login
screen. The forum UI hides the button from signed-out users, yet the URL is
still reachable by shared link, bookmark or crawler.

Re-declaring the route as ``auth="public"`` and redirecting explicitly keeps the
same destination without relying on the broken error path.

The create/save overrides carry ``topic_type`` from the post form onto the
record; see models/forum.py for why a single forum needs it.
"""

from odoo import http
from odoo.http import request
from odoo.addons.website_forum.controllers.website_forum import WebsiteForum
from odoo.addons.tvbo.models.forum import TOPIC_TYPES


class TvboWebsiteForum(WebsiteForum):

    # sitemap=False: making the route public would otherwise let Odoo enumerate
    # it into sitemap.xml, publishing a URL that only ever redirects to login.
    @http.route(['/forum/<model("forum.forum"):forum>/ask'], type='http', auth="public",
                website=True, sitemap=False)
    def forum_post(self, forum, **post):
        if request.env.user._is_public():
            return request.redirect_query('/web/login', {'redirect': request.httprequest.full_path})
        return super().forum_post(forum, **post)

    @http.route()
    def post_create(self, forum, post_parent=None, **post):
        topic_type = post.get('topic_type')
        # Odoo builds the create() values itself, so the choice rides in on the
        # context default rather than through the (ignored) extra kwarg.
        if not post_parent and topic_type in TOPIC_TYPES:
            request.update_context(default_topic_type=topic_type)
        return super().post_create(forum, post_parent=post_parent, **post)

    @http.route()
    def post_save(self, forum, post, **kwargs):
        response = super().post_save(forum, post, **kwargs)
        topic_type = kwargs.get('topic_type')
        if not post.parent_id and topic_type in TOPIC_TYPES and post.can_edit:
            post.topic_type = topic_type
        return response
