from odoo import fields, models


class StudentProject(models.Model):
    """An internship, lab rotation or thesis the lab supervises: who does it, who supervises it, where it stands and when it ends. The student is an employee of type Student or Trainee, and the project belongs to the student's branch."""

    _name = 'lab.student_project'
    _description = 'Student project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char('Topic', required=True, tracking=True)
    kind = fields.Selection([('internship', 'Internship'), ('rotation', 'Lab rotation'), ('bachelor', 'Bachelor thesis'), ('master', 'Master thesis'), ('phd', 'PhD thesis')], required=True, tracking=True)
    student_id = fields.Many2one('hr.employee', string='Student', required=True, index=True, ondelete='restrict', tracking=True)
    company_id = fields.Many2one(related='student_id.company_id', store=True, index=True)
    supervisor_ids = fields.Many2many('res.users', 'lab_student_project_supervisor_rel', 'project_id', 'user_id', string='Supervisors', default=lambda self: self.env.user)
    state = fields.Selection([('planned', 'Planned'), ('running', 'Running'), ('submitted', 'Submitted'), ('done', 'Done')], string='Status', default='planned', required=True, tracking=True, group_expand=True)
    date_start = fields.Date('Start', tracking=True)
    date_end = fields.Date('End', tracking=True, help='The submission deadline of a thesis, or the last day of an internship or rotation.')

    _date_order = models.Constraint('CHECK(date_end IS NULL OR date_start IS NULL OR date_end >= date_start)', 'The end date must not be before the start date.')
