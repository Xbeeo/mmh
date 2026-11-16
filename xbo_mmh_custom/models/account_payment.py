# -*- coding: utf-8 -*-

from odoo import models, fields,api

class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    description = fields.Char(string="Description")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('payment_type') == 'outbound':

                approval = self.env['dynamic.approval'].sudo().search([
                    ('model_id.model', '=', 'account.payment'),
                    ('state', 'in', [
                        'active',
                        'multi_state_activated',
                        'old',
                        'update',
                        'apply',
                    ]),
                    ('company_id', 'in', self.env.company.ids),
                ], limit=1)

                if approval and 'x_approval_id' in self._fields:
                    if not vals.get('x_approval_id'):
                        vals.update({
                            'x_approval_id': approval.id,
                            'x_approve_state': 'approve',
                            'x_need_to_approve': False,
                            'x_multi_state': True,
                        })

        return super().create(vals_list)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):

        res = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance
        )

        for line_vals in res:
            line_vals.update({
                'description': self.description,
            })

        return res

    def action_post(self):
        res = super().action_post()

        for payment in self:
            if payment.payment_type != 'outbound' or payment.state == 'draft':
                continue

            bills = payment.invoice_ids.filtered(lambda m: m.state == 'posted')
            if not bills:
                continue

            domain = [
                ('parent_state', '=', 'posted'),
                ('account_type', '=', 'liability_payable'),
                ('reconciled', '=', False),
            ]
            payment_lines = payment.move_id.line_ids.filtered_domain(domain)
            bill_lines = bills.line_ids.filtered_domain(domain)

            for account in payment_lines.account_id:
                (payment_lines + bill_lines).filtered(
                    lambda l: l.account_id == account and not l.reconciled
                ).reconcile()

        return res