# -*- coding: utf-8 -*-


from odoo import fields, models, api


class HREmployeeInh(models.Model):
    _inherit = 'hr.employee'

    salary = fields.Float(string='Salary', help='Add Faculty Salary')
    employee_code = fields.Char(copy=False, string='Employee Code')
    manual_attendance = fields.Boolean(string='Manual Attendance')

    _employee_code_uniq = models.Constraint(
        'unique(employee_code)', 'Employee code must be unique!')
    
    def write(self, vals):
        res = super().write(vals)
        if 'manual_attendance' in vals:
            self._sync_kiosk_group()
        return res

    def _sync_kiosk_group(self):
        group = self.env.ref('xbo_mmh_custom.group_manual_attendance')
        for emp in self.filtered('user_id'):
            emp.user_id.group_ids = [(4 if emp.manual_attendance else 3, group.id)]
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_kiosk_group()
        return records