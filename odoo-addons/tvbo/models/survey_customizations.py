# -*- coding: utf-8 -*-
"""Platform survey customizations (Odoo `survey` overlay).

Two additions, both kept out of the schema-validated TVBO data:
  1. A per-survey custom **start-button label** (e.g. "Start Exam"), with a
     sensible type-aware default when left blank.
  2. A wizard to **reuse questions from another survey**. Odoo ties every
     ``survey.question`` to exactly one survey (``survey_id`` is a cascade FK),
     so there is no native cross-survey sharing — "reuse" means copying. The
     wizard copies the chosen questions (with their answer options, which carry
     ``copy=True``) into the current survey.
"""
from odoo import api, fields, models


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    start_button_label = fields.Char(
        string='Start button label', translate=True,
        help="Custom text for the public start button (e.g. 'Start Exam'). "
             "Leave empty to use a default based on the survey type "
             "('Start Assessment' for an assessment, otherwise 'Start Survey').")


class SurveyQuestionImport(models.TransientModel):
    _name = 'tvbo.survey.question.import'
    _description = 'Copy questions from another survey into this one'

    target_survey_id = fields.Many2one(
        'survey.survey', string='Target survey', required=True, readonly=True,
        default=lambda self: self.env.context.get('active_id'))
    source_survey_id = fields.Many2one(
        'survey.survey', string='Copy from survey', required=True,
        help="The survey to copy questions from.")
    question_ids = fields.Many2many(
        'survey.question', string='Questions to copy',
        help="Questions copied (with their answer options) into the target survey.")

    @api.onchange('source_survey_id')
    def _onchange_source_survey_id(self):
        """Pre-select all real questions (not section headers) of the source."""
        if self.source_survey_id:
            self.question_ids = self.source_survey_id.question_ids.filtered(
                lambda q: not q.is_page)
        else:
            self.question_ids = False

    def action_import(self):
        self.ensure_one()
        for question in self.question_ids:
            # Copy carries suggested_answer_ids (copy=True); clear page_id so the
            # copy lands at the end of the target survey rather than referencing a
            # section that belongs to the source.
            question.copy({'survey_id': self.target_survey_id.id, 'page_id': False})
        return {'type': 'ir.actions.act_window_close'}
