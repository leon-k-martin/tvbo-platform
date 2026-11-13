# -*- coding: utf-8 -*-
"""Platform survey customizations (Odoo `survey` overlay).

Three additions, all kept out of the schema-validated TVBO data:
  1. A per-survey custom **start-button label** (e.g. "Start Exam"), with a sensible type-aware default when left blank.
  2. A wizard to **reuse questions from another survey**. Odoo ties every ``survey.question`` to exactly one survey (``survey_id`` is a cascade FK), so there is no native cross-survey sharing — "reuse" means copying. The wizard copies the chosen questions (with their answer options, which carry ``copy=True``) into the current survey.
  3. **Country questions** for live sessions: a single-choice question whose answers are the ``res.country`` records, picked from a dropdown by attendees and drawn on a world map on the host screen.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    start_button_label = fields.Char(
        string='Start button label', translate=True,
        help="Custom text for the public start button (e.g. 'Start Exam'). "
             "Leave empty to use a default based on the survey type "
             "('Start Assessment' for an assessment, otherwise 'Start Survey').")


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    is_country_question = fields.Boolean(
        string='Country question',
        help="Answers are the countries of the world, chosen from a dropdown; a live session shows the results on a world map.")

    @api.model_create_multi
    def create(self, vals_list):
        questions = super().create(vals_list)
        questions._fill_country_answers()
        return questions

    def write(self, vals):
        result = super().write(vals)
        if vals.get('is_country_question'):
            self._fill_country_answers()
        return result

    @api.constrains('is_country_question', 'suggested_answer_ids')
    def _check_country_answers(self):
        for question in self.filtered('is_country_question'):
            if any(not answer.country_id for answer in question.suggested_answer_ids):
                raise ValidationError(self.env._("Remove the existing answers of “%s” before making it a country question; its answers become the list of countries.", question.title))

    def _fill_country_answers(self):
        """Give every country question without answers one answer per ``res.country``, sorted by name."""
        questions = self.filtered(lambda q: q.is_country_question and not q.suggested_answer_ids)
        if not questions:
            return
        countries = self.env['res.country'].search([], order='name')
        for question in questions:
            question.question_type = 'simple_choice'
            question.suggested_answer_ids = [
                fields.Command.create({'value': country.name, 'country_id': country.id, 'sequence': index})
                for index, country in enumerate(countries)
            ]


class SurveyQuestionAnswer(models.Model):
    _inherit = 'survey.question.answer'

    country_id = fields.Many2one('res.country', string='Country')


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
        """Copy the chosen questions with their answers to the end of the target survey, detached from the source's sections."""
        self.ensure_one()
        for question in self.question_ids:
            question.copy({'survey_id': self.target_survey_id.id, 'page_id': False})
        return {'type': 'ir.actions.act_window_close'}
