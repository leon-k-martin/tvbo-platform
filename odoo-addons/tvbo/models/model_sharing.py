# -*- coding: utf-8 -*-
"""Platform-only ownership, sharing & **publication workflow** for user content.

Sharing/publication is a *platform* concern, not part of the TVBO data schema: a
model's owner and publication state must never end up in the schema-validated
YAML (the ontology forbids extra fields). So this metadata lives in its own
table, ``tvbo.model_share``, and the schema-generated entities
(``tvbo.dynamics`` / ``tvbo.simulation_experiment`` / ``tvbo.study``) are left
completely untouched — no fields added, nothing to leak into serialization.

Publication is **gated**, not a one-click toggle. A saved element travels a
small state machine before it becomes visible to the community:

    draft ──submit──▶ [automated technical validation]
                          │ pass                 │ fail
                          ▼                       ▼
                      in_review  ◀── resubmit ── (stays draft, issues shown)
                       │      │
                 approve│      │reject
                        ▼      ▼
                   published   changes_requested ──revise & resubmit──▶ …

- **Technical validation** (``run_technical_validation``) runs automatically on
  submit — schema validity, metadata completeness, reference integrity and a
  best-effort runnable smoke-test. It must pass before a human ever sees it.
- **Peer review** is done by internal staff in ``group_tvbo_reviewer``. A single
  reviewer's approval publishes the element; a rejection returns it to the owner
  with a note. Every transition is written to ``tvbo.publication_review`` for an
  auditable trail.

The public-visibility outcome is exposed through the legacy ``visibility`` field
(``shared`` iff ``published``) so the community gallery, the unified Knowledge
Graph and the REST API — all of which key off ``visibility`` — keep working
unchanged. ``visibility`` is now *computed* from ``publication_state``: the state
machine is the single source of truth.
"""
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Publication lifecycle. ``published`` is the only public state.
PUBLICATION_STATES = [
    ('draft', 'Draft'),
    ('in_review', 'In review'),
    ('changes_requested', 'Changes requested'),
    ('published', 'Published'),
]

REVIEWER_GROUP = 'tvbo.group_tvbo_reviewer'

# A share targets exactly one saved element; these are the supported kinds.
_TARGET_FIELDS = {
    'dynamics_id': ('tvbo.dynamics', 'Dynamics', 'model'),
    'experiment_id': ('tvbo.simulation_experiment', 'SimulationExperiment', 'experiment'),
    'study_id': ('tvbo.study', 'Study', 'study'),
}


class ModelShare(models.Model):
    _name = 'tvbo.model_share'
    _description = 'Ownership, sharing & publication metadata for a user-saved element (platform-only)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'write_date desc'

    # ------------------------------------------------------------------ #
    # Target: exactly one saved element (model, experiment or study).
    # Both/all FKs are optional; the constraint below enforces exactly-one.
    # NULLs are distinct in Postgres, so unique(<fk>) acts as one-share-per-
    # target without clashing across the three columns.
    # ------------------------------------------------------------------ #
    dynamics_id = fields.Many2one(
        'tvbo.dynamics', string='Model', ondelete='cascade', index=True,
        help='The saved model this record describes.')
    experiment_id = fields.Many2one(
        'tvbo.simulation_experiment', string='Experiment', ondelete='cascade', index=True,
        help='The saved experiment this record describes.')
    study_id = fields.Many2one(
        'tvbo.study', string='Study', ondelete='cascade', index=True,
        help='The saved study this record describes.')

    owner_user_id = fields.Many2one(
        'res.users', string='Owner', required=True, ondelete='cascade', index=True,
        default=lambda self: self.env.user.id,
        help='User who saved the element.')

    # ------------------------------------------------------------------ #
    # Peer-to-peer sharing (distinct from publishing).
    #
    #   sharing    = grant specific, named collaborators access to *this* copy.
    #                Instant, owner-controlled, NOT peer-reviewed, NOT public.
    #   publishing = make it visible to EVERYONE in the community gallery and
    #                Knowledge Graph. Gated by validation + peer review below.
    #
    # The two are orthogonal: an element can be shared with a colleague while a
    # draft, and it can be published without ever being p2p-shared. Access is the
    # union: owner OR listed collaborator OR published.
    # ------------------------------------------------------------------ #
    shared_user_ids = fields.Many2many(
        'res.users', 'tvbo_model_share_user_rel', 'share_id', 'user_id',
        string='Shared with', copy=False,
        help='Specific people you have granted access to this element. They can '
             'view and load it even while it is private/draft. This is direct '
             'peer-to-peer sharing — it does NOT publish to the community.')
    shared_user_count = fields.Integer(
        string='# collaborators', compute='_compute_shared_user_count')
    access_scope = fields.Selection(
        selection=[('private', 'Private'), ('collaborators', 'Shared with people'),
                   ('public', 'Public')],
        string='Who can access', compute='_compute_access_scope', store=True,
        help='Private: only you. Shared with people: you and named collaborators. '
             'Public: everyone (published).')

    # display_name is provided by base; we only override _compute_display_name below.
    element_kind = fields.Char(compute='_compute_element_kind', store=True,
                               help='model / experiment / study.')

    # ------------------------------------------------------------------ #
    # Publication state machine (the source of truth).
    # ------------------------------------------------------------------ #
    publication_state = fields.Selection(
        selection=PUBLICATION_STATES, string='Publication', default='draft',
        required=True, index=True, tracking=True, copy=False,
        help='Draft: private to the owner. In review: passed automated '
             'validation, awaiting a reviewer. Changes requested: a reviewer '
             'sent it back. Published: approved and visible to everyone.')

    # Legacy effective visibility — computed mirror so every existing read path
    # (community gallery, Knowledge Graph, REST API) keeps working. ``shared``
    # iff the element is published; otherwise ``private``.
    visibility = fields.Selection(
        selection=[('private', 'Private'), ('shared', 'Shared')],
        string='Visibility', compute='_compute_visibility', store=True, index=True,
        help='Derived from the publication state: an element is Shared (public) '
             'only once it has been published. Do not write this directly — drive '
             'the publication_state instead.')

    submitted_date = fields.Datetime(string='Submitted', readonly=True, copy=False)
    published_date = fields.Datetime(string='Published', readonly=True, copy=False)
    reviewer_id = fields.Many2one(
        'res.users', string='Decided by', readonly=True, copy=False,
        help='Reviewer who approved or last decided on this submission.')

    # ------------------------------------------------------------------ #
    # Automated technical validation.
    # ------------------------------------------------------------------ #
    validation_state = fields.Selection(
        selection=[('not_run', 'Not run'), ('passed', 'Passed'), ('failed', 'Failed')],
        string='Validation', default='not_run', required=True, copy=False, tracking=True)
    validation_report = fields.Text(
        string='Validation report (JSON)', readonly=True, copy=False,
        help='Structured result of the last automated technical validation.')
    validation_html = fields.Html(
        string='Validation result', compute='_compute_validation_html', sanitize=False)
    validation_date = fields.Datetime(string='Last validated', readonly=True, copy=False)

    # Reviewer's working note (used by the backend approve/reject buttons).
    review_decision_note = fields.Text(
        string='Reviewer note', copy=False,
        help='Feedback sent to the owner with the review decision. Required when '
             'requesting changes.')

    review_log_ids = fields.One2many(
        'tvbo.publication_review', 'share_id', string='Review history', readonly=True)

    # Odoo 19: SQL constraints are declared as models.Constraint attributes.
    _dynamics_uniq = models.Constraint(
        'unique(dynamics_id)', 'Each model can have only one sharing record.')
    _experiment_uniq = models.Constraint(
        'unique(experiment_id)', 'Each experiment can have only one sharing record.')
    _study_uniq = models.Constraint(
        'unique(study_id)', 'Each study can have only one sharing record.')

    # ------------------------------------------------------------------ #
    # Computes & constraints
    # ------------------------------------------------------------------ #
    @api.depends('publication_state')
    def _compute_visibility(self):
        for share in self:
            share.visibility = 'shared' if share.publication_state == 'published' else 'private'

    @api.depends('shared_user_ids')
    def _compute_shared_user_count(self):
        for share in self:
            share.shared_user_count = len(share.shared_user_ids)

    @api.depends('publication_state', 'shared_user_ids')
    def _compute_access_scope(self):
        for share in self:
            if share.publication_state == 'published':
                share.access_scope = 'public'
            elif share.shared_user_ids:
                share.access_scope = 'collaborators'
            else:
                share.access_scope = 'private'

    @api.depends('dynamics_id', 'experiment_id', 'study_id')
    def _compute_element_kind(self):
        for share in self:
            share.element_kind = next(
                (kind for fname, (_m, _c, kind) in _TARGET_FIELDS.items() if share[fname]),
                False)

    @api.depends('dynamics_id', 'experiment_id', 'study_id', 'publication_state')
    def _compute_display_name(self):
        for share in self:
            target = share.target
            label = (target.display_name if target else _('(empty)')) or _('(unnamed)')
            state = dict(PUBLICATION_STATES).get(share.publication_state, '')
            share.display_name = '%s — %s' % (label, state)

    @api.depends('validation_report')
    def _compute_validation_html(self):
        for share in self:
            share.validation_html = share._render_validation_html()

    @api.constrains('dynamics_id', 'experiment_id', 'study_id')
    def _check_single_target(self):
        for share in self:
            filled = sum(1 for fname in _TARGET_FIELDS if share[fname])
            if filled != 1:
                raise ValidationError(_(
                    'A share must reference exactly one of a model, an experiment '
                    'or a study.'))

    # ------------------------------------------------------------------ #
    # Target helpers
    # ------------------------------------------------------------------ #
    @property
    def res_model(self):
        self.ensure_one()
        return next((m for fname, (m, _c, _k) in _TARGET_FIELDS.items() if self[fname]), False)

    @property
    def target(self):
        """The shared record itself (a dynamics, experiment or study)."""
        self.ensure_one()
        for fname in _TARGET_FIELDS:
            if self[fname]:
                return self[fname]
        return self.env['tvbo.dynamics']

    def _target_meta(self):
        """(odoo_model, pydantic_class, kind) for the current target."""
        self.ensure_one()
        for fname, meta in _TARGET_FIELDS.items():
            if self[fname]:
                return meta
        return (False, False, False)

    # ------------------------------------------------------------------ #
    # Access resolution — the single rule every read path should use.
    # ------------------------------------------------------------------ #
    def is_accessible_to(self, user):
        """True if ``user`` may view/load this element.

        Access is the union of the two sharing mechanisms:
          * the owner, always;
          * a named collaborator (peer-to-peer share);
          * everyone, once the element is published (public).
        """
        self.ensure_one()
        if self.publication_state == 'published':
            return True
        if user and self.owner_user_id.id == user.id:
            return True
        return bool(user) and user.id in self.shared_user_ids.ids

    @api.model
    def hidden_target_ids(self, share_field, user):
        """IDs of ``share_field`` targets this ``user`` must NOT see.

        A saved element is hidden when it is neither published, owned by the
        user, nor shared with them. Ground-truth records (no share row) are never
        hidden. Used to build a negative domain for list/graph queries.
        """
        uid = user.id if user else False
        # NOT published AND NOT (owned by me OR shared with me).
        domain = [(share_field, '!=', False), ('publication_state', '!=', 'published')]
        if uid:
            domain += ['!', '|', ('owner_user_id', '=', uid), ('shared_user_ids', 'in', uid)]
        shares = self.sudo().search(domain)
        return [s[share_field].id for s in shares if s[share_field]]

    # ---- p2p sharing mutations (owner-driven, instant, no review) ---------
    def share_with_users(self, users):
        """Grant a recordset of users access to this element."""
        self.ensure_one()
        self.write({'shared_user_ids': [(4, u.id) for u in users if u]})
        return True

    def unshare_user(self, user):
        """Revoke a collaborator's access."""
        self.ensure_one()
        self.write({'shared_user_ids': [(3, user.id)]})
        return True

    @api.model
    def _resolve_user(self, login_or_email):
        """Find a user by login or email (case-insensitive), or empty recordset."""
        term = (login_or_email or '').strip()
        if not term:
            return self.env['res.users']
        Users = self.env['res.users'].sudo()
        return Users.search(
            ['|', ('login', '=ilike', term), ('email', '=ilike', term)], limit=1)

    # ------------------------------------------------------------------ #
    # Automated technical validation
    # ------------------------------------------------------------------ #
    def run_technical_validation(self):
        """Run every automated gate and persist a structured report.

        Returns the report dict ``{'passed': bool, 'checks': [...]}``. A check
        marked ``skipped`` does not count against the pass/fail decision (e.g. a
        runnable smoke-test on a node without a simulation runtime installed).
        """
        self.ensure_one()
        _model, _cls, kind = self._target_meta()
        checks = [
            self._vcheck_metadata(kind),
            self._vcheck_schema(kind),
            self._vcheck_references(kind),
            self._vcheck_runnable(kind),
        ]
        passed = all(c['ok'] for c in checks if not c.get('skipped'))
        report = {
            'passed': passed,
            'element': kind,
            'checked_at': fields.Datetime.to_string(fields.Datetime.now()),
            'checks': checks,
        }
        self.write({
            'validation_state': 'passed' if passed else 'failed',
            'validation_report': json.dumps(report, default=str),
            'validation_date': fields.Datetime.now(),
        })
        self._log('validate', validation_ok=passed)
        return report

    def _vcheck_metadata(self, kind):
        """Publication needs a human-readable name, a description and attribution."""
        target = self.target
        problems = []
        name = target.display_name or (getattr(target, 'label', False) or getattr(target, 'name', False))
        if not name or not str(name).strip():
            problems.append('a name/label')
        desc = (getattr(target, 'description', '') or '').strip()
        if len(desc) < 20:
            problems.append('a description of at least 20 characters')
        if kind == 'study' and not (getattr(target, 'citekey', '') or getattr(target, 'doi', '')):
            problems.append('a citation key or DOI')
        if not self.owner_user_id:
            problems.append('an owner (attribution)')
        ok = not problems
        return {
            'id': 'metadata', 'label': 'Metadata completeness', 'ok': ok,
            'detail': 'All required metadata present.' if ok
                      else 'Missing: ' + ', '.join(problems) + '.',
        }

    def _vcheck_schema(self, kind):
        """Re-validate the element against the TVBO (LinkML/pydantic) schema."""
        obj, errors = self._validate_against_schema()
        if errors == 'unavailable':
            return {'id': 'schema', 'label': 'Schema validity', 'ok': True, 'skipped': True,
                    'detail': 'Schema validator unavailable in this context; skipped.'}
        if errors == 'not_found':
            return {'id': 'schema', 'label': 'Schema validity', 'ok': False,
                    'detail': 'The element could not be resolved for validation.'}
        if errors:
            preview = self._format_schema_errors(errors)
            return {'id': 'schema', 'label': 'Schema validity', 'ok': False,
                    'detail': 'Does not satisfy the schema: ' + preview}
        return {'id': 'schema', 'label': 'Schema validity', 'ok': True,
                'detail': 'Validates cleanly against the TVBO schema.'}

    def _vcheck_references(self, kind):
        """No referenced building block may be private to another user.

        Publishing an element that embeds someone else's *private* content would
        leak it, so every shareable sub-element it points at must itself be
        public (no share row) or owned by the submitter.
        """
        leaked = self._private_foreign_references()
        if leaked is None:
            return {'id': 'references', 'label': 'Reference integrity', 'ok': True, 'skipped': True,
                    'detail': 'No cross-references to check for this element type.'}
        if leaked:
            names = ', '.join(sorted(leaked))
            return {'id': 'references', 'label': 'Reference integrity', 'ok': False,
                    'detail': 'References private content owned by other users: ' + names + '.'}
        return {'id': 'references', 'label': 'Reference integrity', 'ok': True,
                'detail': 'All referenced building blocks are public or your own.'}

    def _vcheck_runnable(self, kind):
        """Best-effort runnable smoke-test (experiments only).

        Materialises the validated experiment through the ``tvbo`` package and
        attempts a very short run. If no simulation runtime is installed on this
        node, the check is *skipped* (not failed) and the reviewer is prompted to
        run it manually — the web tier is not expected to carry heavy backends.
        """
        if kind != 'experiment':
            return {'id': 'runnable', 'label': 'Runnable smoke-test', 'ok': True, 'skipped': True,
                    'detail': 'Not applicable to a %s.' % (kind or 'element')}
        obj, errors = self._validate_against_schema()
        if errors and errors not in ('unavailable', 'not_found'):
            return {'id': 'runnable', 'label': 'Runnable smoke-test', 'ok': False,
                    'detail': 'Cannot run: the experiment does not validate.'}
        if obj is None:
            return {'id': 'runnable', 'label': 'Runnable smoke-test', 'ok': True, 'skipped': True,
                    'detail': 'Could not materialise the experiment; skipped.'}
        try:
            ran, detail = self._try_short_run(obj)
        except (ImportError, ModuleNotFoundError) as exc:
            return {'id': 'runnable', 'label': 'Runnable smoke-test', 'ok': True, 'skipped': True,
                    'detail': 'No simulation runtime on this node (%s); run manually.' % exc}
        except Exception as exc:  # noqa: BLE001 - a real failure to build/run
            return {'id': 'runnable', 'label': 'Runnable smoke-test', 'ok': False,
                    'detail': 'Failed to run: %s' % exc}
        if ran:
            return {'id': 'runnable', 'label': 'Runnable smoke-test', 'ok': True, 'detail': detail}
        return {'id': 'runnable', 'label': 'Runnable smoke-test', 'ok': True, 'skipped': True,
                'detail': detail}

    # ---- validation internals ---------------------------------------------
    def _validate_against_schema(self):
        """Return ``(pydantic_obj, errors)`` for the target, reusing the
        controller validators. ``errors`` is ``'unavailable'`` when no request
        context is bound, ``'not_found'``/``list``/``None`` otherwise."""
        self.ensure_one()
        _model, cls, kind = self._target_meta()
        try:
            from ..controllers.building_blocks_api import (
                validate_experiment, validate_instance)
        except Exception:  # noqa: BLE001
            return None, 'unavailable'
        try:
            if kind == 'experiment':
                return validate_experiment(self.experiment_id.id)
            return validate_instance(cls, self.target.id)
        except Exception as exc:  # noqa: BLE001 - request-less context, etc.
            _logger.debug('schema validation unavailable: %s', exc)
            return None, 'unavailable'

    def _private_foreign_references(self):
        """Names of directly-referenced elements that are private to *others*.

        Returns ``None`` when the element type has no shareable references to
        check (models/studies), otherwise a (possibly empty) set of labels.
        """
        self.ensure_one()
        if self.element_kind != 'experiment':
            return None
        exp = self.experiment_id
        # Direct many2one references an experiment may embed.
        ref_fields = ('model', 'dynamics', 'network', 'coupling', 'coupling_function',
                      'integrator', 'observation', 'observation_model')
        referenced = []
        for fname in ref_fields:
            if fname in exp._fields and exp[fname]:
                referenced.append(exp[fname])
        leaked = set()
        Share = self.sudo()
        for rec in referenced:
            for item in rec:
                model_name = item._name
                fk = {'tvbo.dynamics': 'dynamics_id',
                      'tvbo.simulation_experiment': 'experiment_id',
                      'tvbo.study': 'study_id'}.get(model_name)
                if not fk:
                    continue
                share = Share.search([(fk, '=', item.id)], limit=1)
                if (share and share.publication_state != 'published'
                        and share.owner_user_id.id != self.owner_user_id.id):
                    leaked.add(item.display_name or model_name)
        return leaked

    def _try_short_run(self, obj):
        """Attempt a minimal simulation; return ``(ran: bool, detail: str)``.

        Kept deliberately defensive: the tvbo runtime API and its heavy backends
        may be absent on the web tier. Any missing runtime raises ImportError,
        which the caller turns into a *skipped* result.
        """
        run = getattr(obj, 'run', None)
        if not callable(run):
            return False, 'This tvbo build exposes no run() entrypoint; skipped.'
        # A tiny run: short simulation length where the API allows it.
        try:
            result = run(simulation_length=1.0)
        except TypeError:
            result = run()
        return True, 'Executed a short simulation without error (%s).' % type(result).__name__

    def _format_schema_errors(self, errors, limit=4):
        if not isinstance(errors, list):
            return str(errors)
        parts = []
        for err in errors[:limit]:
            loc = '.'.join(str(p) for p in err.get('loc', [])) if isinstance(err, dict) else ''
            msg = err.get('msg', str(err)) if isinstance(err, dict) else str(err)
            parts.append(('%s: %s' % (loc, msg)) if loc else msg)
        more = len(errors) - limit
        if more > 0:
            parts.append('… and %d more' % more)
        return '; '.join(parts)

    def _render_validation_html(self):
        self.ensure_one()
        if not self.validation_report:
            return '<p class="text-muted">Not validated yet.</p>'
        try:
            report = json.loads(self.validation_report)
        except (ValueError, TypeError):
            return '<pre>%s</pre>' % (self.validation_report or '')
        rows = []
        for check in report.get('checks', []):
            if check.get('skipped'):
                icon, cls = '⚠︎', 'text-warning'
            elif check.get('ok'):
                icon, cls = '✓', 'text-success'
            else:
                icon, cls = '✗', 'text-danger'
            rows.append(
                '<li><span class="%s"><strong>%s %s</strong></span> — %s</li>'
                % (cls, icon, check.get('label', check.get('id', '')),
                   (check.get('detail') or '')))
        banner = ('<p class="text-success"><strong>All automated checks passed.</strong></p>'
                  if report.get('passed')
                  else '<p class="text-danger"><strong>Automated validation failed.</strong> '
                       'Fix the items below and resubmit.</p>')
        return banner + '<ul>' + ''.join(rows) + '</ul>'

    # ------------------------------------------------------------------ #
    # Workflow transitions
    # ------------------------------------------------------------------ #
    def submit_for_review(self):
        """Owner action: validate, then queue for peer review if it passes.

        Returns ``{'success': bool, 'state': str, 'report': {...}}``. On a
        validation failure the element stays in ``draft`` and the report holds
        the actionable issues.
        """
        self.ensure_one()
        if self.publication_state == 'in_review':
            return {'success': True, 'state': 'in_review',
                    'report': self._last_report(), 'message': 'Already awaiting review.'}
        if self.publication_state == 'published':
            return {'success': False, 'state': 'published',
                    'message': 'Already published. Withdraw it first to revise.'}
        report = self.run_technical_validation()
        if not report['passed']:
            return {'success': False, 'state': self.publication_state, 'report': report,
                    'message': 'Automated validation failed. Please fix the issues and resubmit.'}
        self.write({'publication_state': 'in_review', 'submitted_date': fields.Datetime.now()})
        self._log('submit')
        self._subscribe_owner()
        self._notify_reviewers()
        return {'success': True, 'state': 'in_review', 'report': report,
                'message': 'Submitted for peer review.'}

    def withdraw(self):
        """Owner action: pull a submission or a published element back to draft."""
        self.ensure_one()
        if self.publication_state == 'draft':
            return {'success': True, 'state': 'draft'}
        self.write({'publication_state': 'draft'})
        self._log('withdraw')
        try:
            self.activity_feedback(['mail.mail_activity_data_todo'])
        except Exception:  # noqa: BLE001 - mail infra optional
            pass
        return {'success': True, 'state': 'draft'}

    def action_approve(self, note=None):
        """Reviewer action: approve and publish."""
        self._ensure_reviewer()
        for share in self:
            if share.publication_state != 'in_review':
                raise UserError(_('Only submissions awaiting review can be approved.'))
            share.write({
                'publication_state': 'published',
                'published_date': fields.Datetime.now(),
                'reviewer_id': self.env.user.id,
            })
            share._log('approve', note=note or share.review_decision_note)
            share._close_activities()
            share._notify_owner(
                _('Your submission “%s” was approved and is now published.')
                % (share.target.display_name or ''), note)
        return True

    def action_reject(self, note=None):
        """Reviewer action: send back to the owner with required feedback."""
        self._ensure_reviewer()
        for share in self:
            reason = note or share.review_decision_note
            if not reason or not str(reason).strip():
                raise UserError(_('A note is required when requesting changes.'))
            if share.publication_state != 'in_review':
                raise UserError(_('Only submissions awaiting review can be sent back.'))
            share.write({'publication_state': 'changes_requested', 'reviewer_id': self.env.user.id})
            share._log('reject', note=reason)
            share._close_activities()
            share._notify_owner(
                _('Your submission “%s” needs changes before it can be published.')
                % (share.target.display_name or ''), reason)
        return True

    # ---- backend button wrappers (raise so the client shows a dialog) ------
    def button_submit(self):
        self.ensure_one()
        result = self.submit_for_review()
        if not result.get('success'):
            raise UserError(result.get('message') or _('Submission failed.'))
        return True

    def button_approve(self):
        return self.action_approve()

    def button_reject(self):
        return self.action_reject()

    def button_revalidate(self):
        self.ensure_one()
        self.run_technical_validation()
        return True

    # ------------------------------------------------------------------ #
    # Notifications / audit
    # ------------------------------------------------------------------ #
    def _ensure_reviewer(self):
        if self.env.su:
            return
        if not self.env.user.has_group(REVIEWER_GROUP):
            raise UserError(_('Only reviewers can decide on publication requests.'))

    def _reviewers(self):
        group = self.env.ref(REVIEWER_GROUP, raise_if_not_found=False)
        # Odoo 19: ``all_user_ids`` is the transitive membership (direct members
        # PLUS everyone who inherits the group via implication, e.g. admins from
        # base.group_system). ``user_ids`` alone would miss inherited reviewers.
        return group.all_user_ids if group else self.env['res.users']

    def _log(self, action, note=None, validation_ok=None):
        self.ensure_one()
        self.env['tvbo.publication_review'].sudo().create({
            'share_id': self.id,
            'action': action,
            'actor_id': self.env.uid,
            'note': note or False,
            'validation_ok': validation_ok,
        })

    def _last_report(self):
        try:
            return json.loads(self.validation_report) if self.validation_report else {}
        except (ValueError, TypeError):
            return {}

    def _subscribe_owner(self):
        try:
            if self.owner_user_id.partner_id:
                self.message_subscribe(partner_ids=self.owner_user_id.partner_id.ids)
        except Exception:  # noqa: BLE001
            pass

    def _notify_reviewers(self):
        """Post a message and drop a to-do activity in each reviewer's inbox."""
        try:
            self.message_post(body=_('Submitted for peer review by %s.') % self.owner_user_id.name)
        except Exception:  # noqa: BLE001
            pass
        for reviewer in self._reviewers()[:25]:
            try:
                self.activity_schedule(
                    'mail.mail_activity_data_todo', user_id=reviewer.id,
                    summary=_('Review publication request'),
                    note=_('%s submitted “%s” for publication.') % (
                        self.owner_user_id.name, self.target.display_name or ''))
            except Exception:  # noqa: BLE001 - mail infra optional
                break

    def _notify_owner(self, subject, note):
        body = subject + (('<br/><em>%s</em>' % note) if note else '')
        try:
            self.message_post(body=body,
                              partner_ids=self.owner_user_id.partner_id.ids
                              if self.owner_user_id.partner_id else None)
        except Exception:  # noqa: BLE001
            pass

    def _close_activities(self):
        try:
            self.activity_feedback(['mail.mail_activity_data_todo'])
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # Deletion
    # ------------------------------------------------------------------ #
    def purge_model(self):
        """Delete the linked element (and a model's exclusive children).

        Removing the target cascades to this share row (ondelete='cascade').
        """
        for share in self:
            if share.dynamics_id:
                share.dynamics_id.purge_saved_model()
            elif share.experiment_id:
                share.experiment_id.unlink()
            elif share.study_id:
                share.study_id.unlink()


class PublicationReview(models.Model):
    """Append-only audit trail: one row per publication-workflow action."""
    _name = 'tvbo.publication_review'
    _description = 'Publication workflow audit-trail entry'
    _order = 'create_date desc, id desc'

    share_id = fields.Many2one(
        'tvbo.model_share', string='Submission', required=True,
        ondelete='cascade', index=True)
    action = fields.Selection([
        ('validate', 'Validation run'),
        ('submit', 'Submitted for review'),
        ('approve', 'Approved & published'),
        ('reject', 'Changes requested'),
        ('withdraw', 'Withdrawn'),
    ], required=True, string='Action')
    actor_id = fields.Many2one(
        'res.users', string='By', required=True,
        default=lambda self: self.env.uid, index=True)
    note = fields.Text(string='Note')
    validation_ok = fields.Boolean(string='Validation passed')


class Dynamics(models.Model):
    # Method-only overlay: NO fields are added to the schema entity (so nothing
    # leaks into the schema-validated serialization). These helpers tidy up the
    # parameter/state-variable/equation/range records a user-saved model creates
    # for itself, which would otherwise be orphaned on update or delete.
    _inherit = 'tvbo.dynamics'

    def _saved_model_children(self):
        """The child records a user-saved model owns exclusively.

        The builder always creates fresh parameter/state-variable/etc. records
        per save, so these belong to this model alone and are safe to drop.
        """
        self.ensure_one()
        params = self.parameters | self.coupling_terms
        svs = self.state_variables
        dvs = self.derived_variables
        return {
            'params': params,
            'svs': svs,
            'dvs': dvs,
            'ranges': params.mapped('domain') | svs.mapped('domain'),
            'equations': svs.mapped('equation') | dvs.mapped('equation'),
        }

    def _unlink_saved_children(self, children):
        """Unlink a previously collected child set (parents before nested)."""
        for key in ('params', 'svs', 'dvs', 'ranges', 'equations'):
            for child in children.get(key, self.env['tvbo.dynamics']):
                try:
                    child.unlink()
                except Exception:  # noqa: BLE001 - best-effort cleanup
                    pass

    def purge_saved_model(self):
        """Delete this user-saved model together with its exclusive children."""
        for record in self:
            children = record._saved_model_children()
            record.unlink()
            # record is gone now; unlink the captured children directly.
            for key in ('params', 'svs', 'dvs', 'ranges', 'equations'):
                for child in children.get(key) or []:
                    try:
                        child.unlink()
                    except Exception:  # noqa: BLE001 - best-effort cleanup
                        pass
