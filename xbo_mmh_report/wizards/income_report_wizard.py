
from collections import defaultdict

from odoo import models, fields


class IncomeReportWizard(models.TransientModel):
    _name = 'income.report.wizard'
    _description = 'Income Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    def _get_invoices(self):
        self.ensure_one()

        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel'),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]

        return self.env['account.move'].search(
            domain, order='invoice_date, id'
        )

    def _get_report_data(self):
        self.ensure_one()

        invoices = self._get_invoices()

        section_types = [
            ('opd', 'OPD'),
            ('tests', 'Tests'),
            ('indoor', 'Indoor'),
        ]

        grouped_data = {
            key: defaultdict(lambda: {
                'patients': set(),
                'amount': 0.0,
            })
            for key, name in section_types
        }

        for inv in invoices:

            department = inv.department_id

            # LAB TEST INVOICES
            if inv.is_lab_test:

                section = 'tests'

                # Get products from invoice lines
                for invoice_line in inv.invoice_line_ids:

                    if invoice_line.display_type != 'product':
                        continue

                    product = invoice_line.product_id

                    if not product:
                        continue

                    product_name = product.name

                    data = grouped_data[section][product_name]

                    # Unique patient count for each test
                    if inv.partner_id:
                        data['patients'].add(inv.partner_id.id)

                    # Sum product line amount
                    data['amount'] += invoice_line.price_subtotal

            # OPD INVOICES
            elif department and department.type == 'opd':

                section = 'opd'
                department_name = department.name

                data = grouped_data[section][department_name]

                if inv.partner_id:
                    data['patients'].add(inv.partner_id.id)

                data['amount'] += inv.amount_total

            # INDOOR INVOICES
            elif department and department.type == 'indoor':

                section = 'indoor'
                department_name = department.name

                data = grouped_data[section][department_name]

                if inv.partner_id:
                    data['patients'].add(inv.partner_id.id)

                data['amount'] += inv.amount_total

            else:
                continue

        sections = []
        grand_total = 0.0

        for key, section_name in section_types:

            rows = []
            section_total = 0.0

            for name, values in sorted(grouped_data[key].items()):
                amount = values['amount']
                section_total += amount

                rows.append({
                    'name': name,
                    'patients': len(values['patients']),
                    'amount': amount,
                })

            grand_total += section_total

            sections.append({
                'name': section_name,
                'rows': rows,
                'total': section_total,
            })

        return {
            'sections': sections,
            'grand_total': grand_total,
        }

    def action_print(self):
        return self.env.ref(
            'xbo_mmh_report.action_income_report'
        ).report_action(self)
