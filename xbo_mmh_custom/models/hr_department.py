from odoo import models , api ,fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.osv import expression


class HrDepartmentInherit(models.Model):
    _inherit = "hr.department"

    treatment_rate_line = fields.One2many("treatment.rate.line", "department_id", string="Treatment Type Rate Line")
    type = fields.Selection([
        ('opd', 'OPD'),
        ('indoor', 'Indoor'),
    ], string='Type', default='opd', tracking=True)



class TreatmentRateLine(models.Model):
    _name = "treatment.rate.line"

    department_id = fields.Many2one("hr.department", string="Department")
    doctor_id = fields.Many2one("res.partner", string="Doctor")
    treatment_type_id = fields.Many2one("treatment.type", string="Treatment Type")
    treatment_fees = fields.Float(string="Treatment Fees")

