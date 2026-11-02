import base64
import io
import re

import xlsxwriter

from odoo import fields, models
from odoo.exceptions import ValidationError


class PatientAnalysisWizard(models.TransientModel):
    _name = 'patient.analysis.wizard'
    _description = 'Patient Analysis Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    age_from = fields.Integer()
    age_to = fields.Integer()
    sex = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('both', 'Both')],
        default='both', required=True)

    @staticmethod
    def _to_age(val):
        """age may be a number or text like '25 Years'; returns int or None"""
        if isinstance(val, (int, float)):
            return int(val)
        m = re.match(r'\s*(\d+)', val or '')
        return int(m.group(1)) if m else None

    def action_print(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise ValidationError("Date From must be before Date To.")
        if self.age_to and self.age_from > self.age_to:
            raise ValidationError("Age From must be less than Age To.")

        moves = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ])
        patients = self.env['medical.patient'].search(
            [('patient_id', 'in', moves.partner_id.ids)])
        valid = set()
        for p in patients:
            if self.sex != 'both' and not str(p.sex or '').lower().startswith(self.sex[0]):
                continue
            age = self._to_age(p.age)
            if self.age_from and (age is None or age < self.age_from):
                continue
            if self.age_to and (age is None or age > self.age_to):
                continue
            valid.add(p.patient_id.id)
        moves = moves.filtered(lambda m: m.partner_id.id in valid)

        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf, {'in_memory': True})
        ws = wb.add_worksheet('Patient Analysis')
        bold = wb.add_format({'bold': True})
        title = wb.add_format({'bold': True, 'font_size': 14})
        num = wb.add_format({'num_format': '#,##0.00'})
        ws.write(0, 0, 'Patient Analysis: %s to %s' % (
            self.date_from.strftime('%d %b %Y'), self.date_to.strftime('%d %b %Y')), title)
        for c, h in enumerate(['Sex', 'Age From', 'Age To', 'No. of Patients', 'Total Amount']):
            ws.write(2, c, h, bold)
            ws.set_column(c, c, 18)
        ws.write(3, 0, dict(self._fields['sex'].selection)[self.sex])
        ws.write(3, 1, self.age_from or '')
        ws.write(3, 2, self.age_to or '')
        ws.write_number(3, 3, len(valid))
        ws.write_number(3, 4, sum(moves.mapped('amount_total')), num)
        wb.close()

        att = self.env['ir.attachment'].create({
            'name': 'Patient_Analysis_%s_%s.xlsx' % (self.date_from, self.date_to),
            'type': 'binary',
            'datas': base64.b64encode(buf.getvalue()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % att.id,
                'target': 'self'}