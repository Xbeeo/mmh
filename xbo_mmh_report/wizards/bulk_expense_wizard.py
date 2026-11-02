import base64
import io

import xlsxwriter

from odoo import models, fields


class BulkExpenseWizard(models.TransientModel):
    _name = 'bulk.expense.wizard'
    _description = 'Bulk Expense Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    account_id = fields.Many2one('account.account', string='Account')
    product_id = fields.Many2one(
        'product.product', string='Category',
        domain=[('can_be_expensed', '=', True)])

    file_data = fields.Binary(readonly=True)
    file_name = fields.Char(readonly=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('posted', 'Posted'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('refused', 'Refused'),
        ],
        string="Status",
    )

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def _get_expenses(self):
        self.ensure_one()
        domain = [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        if self.employee_id:
            domain.append(('employee_id', '=', self.employee_id.id))
        # if self.department_id:
        #     domain.append(('employee_id.department_id', '=', self.department_id.id))
        if self.account_id:
            domain.append(('account_id', '=', self.account_id.id))
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.state:
            domain.append(('state', '=', self.state))

        return self.env['hr.expense'].search(domain, order='date, id')

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    def action_print(self):
        return self.env.ref('xbo_mmh_report.action_bulk_expense_report').report_action(self)

    # ------------------------------------------------------------------
    # Excel (no unit price / qty / taxes)
    # ------------------------------------------------------------------
    def action_print_excel(self):
        self.ensure_one()
        lines = self._get_expenses()

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet('Expense Report')

        title = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        sub = wb.add_format({'bold': True, 'align': 'center'})
        head = wb.add_format({'bold': True, 'border': 1, 'bg_color': '#D9D9D9', 'align': 'center'})
        text = wb.add_format({'border': 1})
        num = wb.add_format({'border': 1, 'num_format': '#,##0.00'})
        tot_lbl = wb.add_format({'bold': True, 'border': 1, 'align': 'right'})
        tot_num = wb.add_format({'bold': True, 'border': 1, 'num_format': '#,##0.00'})

        headers = ['Sr#', 'Date', 'Employee', 'Description', 'Total', 'Paid By','Status']
        last_col = len(headers) - 1

        ws.merge_range(0, 0, 0, last_col, 'Expense Report', title)
        ws.merge_range(
            1, 0, 1, last_col,
            'From: %s    To: %s' % (
                self.date_from.strftime('%d %B %Y'),
                self.date_to.strftime('%d %B %Y')),
            sub)

        row = 3
        for col, h in enumerate(headers):
            ws.write(row, col, h, head)

        total = 0.0
        for idx, l in enumerate(lines, start=1):
            row += 1
            total += l.untaxed_amount_currency
            ws.write(row, 0, idx, text)
            ws.write(row, 1, l.date.strftime('%d %B %Y') if l.date else '', text)
            ws.write(row, 2, l.employee_id.name or '', text)
            ws.write(row, 3, l.name or '', text)
            ws.write(row, 4, l.untaxed_amount_currency, num)
            ws.write(row, 5, 'Employee' if l.payment_mode == 'own_account' else 'Company', text)
            ws.write(row, 6, dict(l._fields['state'].selection).get(l.state, ''), text)

        row += 1
        ws.merge_range(row, 0, row, 3, 'Total', tot_lbl)
        ws.write(row, 4, total, tot_num)

        ws.set_column(0, 0, 6)
        ws.set_column(1, 1, 16)
        ws.set_column(2, 2, 25)
        ws.set_column(3, 3, 40)
        ws.set_column(4, 4, 16)
        ws.set_column(5, 5, 12)
        wb.close()

        self.write({
            'file_data': base64.b64encode(output.getvalue()),
            'file_name': 'Expense_Report_%s_to_%s.xlsx' % (self.date_from, self.date_to),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=%s&id=%s&field=file_data&filename_field=file_name&download=true'
                   % (self._name, self.id),
            'target': 'self',
        }