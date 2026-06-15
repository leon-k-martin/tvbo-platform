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
from odoo import fields, models


class ModelShare(models.Model):
    _name = 'tvbo.model_share'
    _description = 'Ownership and sharing metadata for a user-saved model (platform-only)'
    _rec_name = 'dynamics_id'

    dynamics_id = fields.Many2one(
        'tvbo.dynamics',
        string='Model',
        required=True,
        ondelete='cascade',
        index=True,
        help='The saved model this ownership/sharing record describes.',
    )
    owner_user_id = fields.Many2one(
        'res.users',
        string='Owner',
        required=True,
        ondelete='cascade',
        index=True,
        help='User who saved the model through the builder.',
    )
    visibility = fields.Selection(
        selection=[('private', 'Private'), ('shared', 'Shared')],
        string='Visibility',
        default='private',
        required=True,
        index=True,
        help='Private models are visible only to their owner. Shared models '
             'appear in the community gallery for every logged-in user.',
    )

    # Odoo 19: SQL constraints are declared as models.Constraint attributes.
    _dynamics_uniq = models.Constraint(
        'unique(dynamics_id)',
        'Each model can have only one sharing record.',
    )

    def purge_model(self):
        """Delete the linked model (and its exclusive child records).

        Removing the dynamics cascades to this share row (ondelete='cascade').
        """
        for share in self:
            share.dynamics_id.purge_saved_model()


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
