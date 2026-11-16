# -*- coding: utf-8 -*-

from odoo import models, fields, Command, api

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        moves = self.line_ids.move_id

        payments = super()._create_payments()

        if self.payment_type == 'outbound':
            posted_payments = payments.filtered(
                lambda p: p.state != 'draft'
            )
            if posted_payments:
                posted_payments.action_draft()

            # Unreconcile bill payable lines
            moves.line_ids.filtered(
                lambda l: l.account_type == 'liability_payable'
            ).remove_move_reconcile()

            # Keep payment links for Payments smart button
            moves.matched_payment_ids = [
                Command.link(p.id) for p in payments
            ]

            self.env.flush_all()
            moves.invalidate_recordset()
            moves._compute_amount()
            moves._compute_payment_state()

        return payments
