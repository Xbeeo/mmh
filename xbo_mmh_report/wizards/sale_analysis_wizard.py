
import base64
import io

import xlsxwriter

from odoo import fields, models
from odoo.exceptions import ValidationError


class SaleAnalysisWizard(models.TransientModel):
    _name = 'sale.analysis.wizard'
    _description = 'Sale Analysis Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    department_id = fields.Many2one('hr.department')
    dispensary_id = fields.Many2one('pos.config', string='Dispensary')
    patient_id = fields.Many2one('medical.patient')
    doctor_id = fields.Many2one('medical.physician')
    item_id = fields.Many2one('product.product', string='Item')

    def action_print(self):
        self.ensure_one()

        if not (
            self.department_id or self.dispensary_id
            or self.patient_id or self.doctor_id or self.item_id
        ):
            raise ValidationError(
                "Select at least one of Department, Dispensary, Patient, Doctor or Item."
            )

        if self.date_from > self.date_to:
            raise ValidationError("Date From must be before Date To.")

        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]

        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))

        if self.patient_id:
            domain.append(('partner_id', '=', self.patient_id.patient_id.id))

        if self.doctor_id:
            domain.append(('doctor_id', '=', self.doctor_id.partner_id.id))

        if self.item_id:
            domain.append(('invoice_line_ids.product_id', '=', self.item_id.id))

        moves = self.env['account.move'].search(
            domain, order='invoice_date'
        )

        if self.dispensary_id:
            name = (self.dispensary_id.name or '').strip()
            moves = moves.filtered(
                lambda m: (m.ref or '').split('-')[0].strip() == name
            )

        only_item = bool(self.item_id) and not (
            self.department_id or self.dispensary_id
            or self.patient_id or self.doctor_id
        )

        only_patient = bool(self.patient_id) and not (
            self.department_id or self.dispensary_id
            or self.doctor_id or self.item_id
        )

        data = {}

        for m in moves:
            key = (
                m.invoice_date,
                (m.department_id.display_name or '')
                if only_patient else ''
            )

            d = data.setdefault(
                key,
                {'patients': set(), 'amount': 0.0}
            )

            d['patients'].add(m.partner_id.id)

            if self.item_id:
                d['amount'] += sum(
                    l.price_total
                    for l in m.invoice_line_ids
                    if l.product_id == self.item_id
                )
            else:
                d['amount'] += m.amount_total

        # Selected filters
        filters = [
            (label, rec.display_name)
            for label, rec in (
                ('Department', self.department_id),
                ('Dispensary', self.dispensary_id),
                ('Patient', self.patient_id),
                ('Doctor', self.doctor_id),
                ('Item', self.item_id),
            )
            if rec
        ]

        # Create Excel workbook
        buf = io.BytesIO()

        wb = xlsxwriter.Workbook(buf, {'in_memory': True})

        ws = wb.add_worksheet('Sale Analysis')

        # Formats
        bold = wb.add_format({'bold': True})

        title = wb.add_format({
            'bold': True,
            'font_size': 14,
        })

        num = wb.add_format({
            'num_format': '#,##0.00'
        })

        dfmt = wb.add_format({
            'num_format': 'dd mmm yyyy',
            'align': 'left'
        })

        # Title
        ws.write(
            0, 0,
            'Sale Analysis: %s to %s' % (
                self.date_from.strftime('%d %b %Y'),
                self.date_to.strftime('%d %b %Y')
            ),
            title
        )

        # Printed By and Printed On
        now = fields.Datetime.context_timestamp(
            self,
            fields.Datetime.now()
        )

        ws.write(1, 0, 'Printed By', bold)
        ws.write(1, 1, self.env.user.name)

        ws.write(2, 0, 'Printed On', bold)
        ws.write(
            2, 1,
            now.strftime('%d %B %Y %H:%M:%S')
        )

        # Headers
        extra = (
            ['Department'] if only_patient
            else ([] if only_item else ['No. of Patients'])
        )

        headers = (
            ['Date']
            + [f[0] for f in filters]
            + extra
            + ['Total Amount']
        )

        for c, h in enumerate(headers):
            ws.write(4, c, h, bold)
            ws.set_column(c, c, 22)

        # Data rows
        row = 5

        for key in sorted(data):
            day = key[0]

            ws.write_datetime(
                row, 0,
                fields.Datetime.to_datetime(day),
                dfmt
            )

            for c, f in enumerate(filters, start=1):
                ws.write(row, c, f[1])

            n = len(filters) + 1

            if only_patient:
                ws.write(row, n, key[1])
                n += 1

            elif not only_item:
                ws.write_number(
                    row, n,
                    len(data[key]['patients'])
                )
                n += 1

            ws.write_number(
                row, n,
                data[key]['amount'],
                num
            )

            row += 1

        # Close workbook
        wb.close()

        # Create attachment
        att = self.env['ir.attachment'].create({
            'name': 'Sale_Analysis_%s_%s.xlsx' % (
                self.date_from,
                self.date_to
            ),
            'type': 'binary',
            'datas': base64.b64encode(buf.getvalue()),
            'mimetype': (
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            ),
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % att.id,
            'target': 'self',
        }
