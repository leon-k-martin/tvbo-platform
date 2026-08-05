# -*- coding: utf-8 -*-
"""One forum whose posts carry their own kind.

Odoo separates Q&A from open discussion by creating two ``forum.forum``
records, which is what puts a room picker in front of ``/forum``. TVBO runs a
single forum in ``discussions`` mode — so a thread can go back and forth as
often as it needs — and moves the distinction onto the post itself: a Question
can have one reply accepted as the answer, a Discussion simply stays open.
Odoo's ``/forum`` controller redirects straight to the forum as soon as only one
is active, so collapsing the rooms is what removes the gate.
"""

from odoo import api, fields, models
from odoo.fields import Domain

TOPIC_TYPES = ('question', 'discussion')

# ?filters=… values that narrow the index to a single kind of topic.
FILTER_TOPIC_TYPES = {'questions': 'question', 'discussions': 'discussion'}

RETIRED_FORUM_XMLIDS = ('website_forum.forum_help', 'tvbo.forum_help')


class ForumForum(models.Model):
    _inherit = 'forum.forum'

    @api.model
    def _tvbo_retire_split_forums(self):
        """Fold Odoo's demo forum and the pre-merge Help room into the single
        TVBO forum, carrying their posts and tags across before archiving them.

        Runs from data/forum_data.xml on every ``-u tvbo`` and no-ops once the
        retired xmlids are gone, so a fresh database never creates them.
        """
        unified = self.env.ref('tvbo.forum_community', raise_if_not_found=False)
        if not unified:
            return
        retired = self.browse([
            forum.id for xmlid in RETIRED_FORUM_XMLIDS
            if (forum := self.env.ref(xmlid, raise_if_not_found=False)) and forum != unified
        ])
        if not retired:
            return

        posts = self.env['forum.post'].sudo().with_context(active_test=False).search(
            [('forum_id', 'in', retired.ids)])
        posts.forum_id = unified

        Tag = self.env['forum.tag'].sudo()
        for tag in Tag.search([('forum_id', 'in', retired.ids)]):
            # forum.tag carries a unique (name, forum_id), so a same-named tag
            # on the survivor has to absorb this one rather than move next to it.
            twin = Tag.search(
                [('forum_id', '=', unified.id), ('name', '=ilike', tag.name)], limit=1)
            if twin:
                twin.post_ids |= tag.post_ids
                tag.unlink()
            else:
                tag.forum_id = unified

        retired.sudo().active = False


class ForumPost(models.Model):
    _inherit = 'forum.post'

    topic_type = fields.Selection(
        [('question', 'Question'), ('discussion', 'Discussion')],
        string='Topic Type', default='question', required=True, index=True,
        help='Question: one reply can be accepted as the answer. '
             'Discussion: an open thread with nothing to accept.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('parent_id'):
                vals['topic_type'] = self.browse(vals['parent_id']).sudo().topic_type
        return super().create(vals_list)

    @api.model
    def _search_get_detail(self, website, order, options):
        """Add the two topic filters, and keep solved/unsolved off discussions —
        a thread with nothing to accept is not an unsolved problem."""
        detail = super()._search_get_detail(website, order, options)
        filters = options.get('filters')
        topic_type = FILTER_TOPIC_TYPES.get(filters) or ('question' if filters in ('solved', 'unsolved') else None)
        if topic_type:
            detail['base_domain'] = detail['base_domain'] + [Domain('topic_type', '=', topic_type)]
        return detail
