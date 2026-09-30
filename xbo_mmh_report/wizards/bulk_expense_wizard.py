from odoo import models, fields


class BulkExpenseWizard(models.TransientModel):
    _name = 'bulk.expense.wizard'
    _description = 'Bulk Expense Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')

    def action_print(self):
        return self.env.ref('xbo_mmh_report.action_bulk_expense_report').report_action(self)

    def _get_expenses(self):
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        if self.employee_id:
            domain.append(('employee_id', '=', self.employee_id.id))
        return self.env['hr.expense'].search(domain, order='date, id')