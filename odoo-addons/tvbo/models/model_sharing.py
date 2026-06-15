# -*- coding: utf-8 -*-
"""Platform-only ownership & sharing for user-saved models.

Sharing is a *platform* concern, not part of the TVBO data schema: a model's
owner and private/shared state must never end up in the schema-validated YAML
(the ontology forbids extra fields). So this metadata lives in its own table,
``tvbo.model_share``, and the schema-generated ``tvbo.dynamics`` entity is left
completely untouched — no fields added, nothing to leak into serialization.

One share row per saved model:
- seeded ground-truth models have no share row and are public;
- saving a model in the builder creates a row owned by the saver, ``private``;
- the owner can flip it to ``shared`` to expose it in the community gallery.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ModelShare(models.Model):
    _name = 'tvbo.model_share'
    _description = 'Ownership and sharing metadata for a user-saved element (platform-only)'
    _rec_name = 'owner_user_id'

    # A share targets exactly one saved element: a model (Dynamics) or a
    # SimulationExperiment. Both FKs are optional; the constraint below enforces
    # exactly-one. NULLs are distinct in Postgres, so unique(dynamics_id) /
    # unique(experiment_id) act as one-share-per-target without clashing.
    dynamics_id = fields.Many2one(
        'tvbo.dynamics', string='Model', ondelete='cascade', index=True,
        help='The saved model this ownership/sharing record describes.',
    )
    experiment_id = fields.Many2one(
        'tvbo.simulation_experiment', string='Experiment', ondelete='cascade', index=True,
        help='The saved experiment this ownership/sharing record describes.',
    )
    owner_user_id = fields.Many2one(
        'res.users', string='Owner', required=True, ondelete='cascade', index=True,
        help='User who saved the element.',
    )
    visibility = fields.Selection(
        selection=[('private', 'Private'), ('shared', 'Shared')],
        string='Visibility', default='private', required=True, index=True,
        help='Private elements are visible only to their owner. Shared elements '
             'appear in the community gallery for every logged-in user.',
    )

    # Odoo 19: SQL constraints are declared as models.Constraint attributes.
    _dynamics_uniq = models.Constraint(
        'unique(dynamics_id)', 'Each model can have only one sharing record.')
    _experiment_uniq = models.Constraint(
        'unique(experiment_id)', 'Each experiment can have only one sharing record.')

    @api.constrains('dynamics_id', 'experiment_id')
    def _check_single_target(self):
        for share in self:
            if bool(share.dynamics_id) == bool(share.experiment_id):
                raise ValidationError(
                    'A share must reference exactly one of a model or an experiment.')

    @property
    def res_model(self):
        self.ensure_one()
        return 'tvbo.dynamics' if self.dynamics_id else 'tvbo.simulation_experiment'

    @property
    def target(self):
        """The shared record itself (a dynamics or an experiment)."""
        self.ensure_one()
        return self.dynamics_id or self.experiment_id

    def purge_model(self):
        """Delete the linked element (and a model's exclusive children).

        Removing the target cascades to this share row (ondelete='cascade').
        """
        for share in self:
            if share.dynamics_id:
                share.dynamics_id.purge_saved_model()
            elif share.experiment_id:
                share.experiment_id.unlink()


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
