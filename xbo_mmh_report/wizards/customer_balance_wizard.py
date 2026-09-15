from odoo import models, fields

class CustomerBalanceWizard(models.TransientModel):
    _name = 'customer.balance.wizard'
    _description = 'Customer Current Balance Wizard'

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    customer_id = fields.Many2one('res.partner', string='Customer', domain=[('customer_rank', '>', 0)])

    def _get_balance(self, partner):
        lines = self.env['account.move.line'].search([
            ('partner_id', '=', partner.id),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('date', '<=', self.date_to),
            ('parent_state', '!=', 'cancelled'),
        ])
        return sum(lines.mapped('debit')) - sum(lines.mapped('credit'))

    def action_print_report(self):
        if self.customer_id:
            partners = self.customer_id
        else:
            partners = self.env['res.partner'].search([('customer_rank', '>', 0)])

        lines = []
        for p in partners:
            balance = self._get_balance(p)
            if balance <= 0:
                continue
            address = ', '.join(filter(None, [p.street, p.street2, p.city, p.country_id.name]))
            lines.append({
                'type': 'Customers',
                'name': p.name,
                'address': address,
                'phone': getattr(p, 'mobile', False) or p.phone or '',
                'balance': balance,
            })
        data = {'date_from': self.date_from, 'date_to': self.date_to, 'lines': lines}
        return self.env.ref('xbo_mmh_report.action_customer_balance_report').report_action(self, data=data)