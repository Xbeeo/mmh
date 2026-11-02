from odoo import fields, models, _
from odoo.exceptions import UserError


class HrLoanFixedInstallmentWizard(models.TransientModel):
    _name = 'hr.loan.fixed.installment.wizard'
    _description = 'Fixed Installment Wizard'

    loan_id = fields.Many2one(
        'hr.loan',
        string='Loan',
        required=True,
        readonly=True,
    )

    installment_id = fields.Many2one(
        'hr.loan.line',
        string='Installment',
        required=True,
        domain="[('loan_id', '=', loan_id), ('paid', '=', False)]",
    )
    payment_date = fields.Date(
        string='Payment Date',
        related='installment_id.date',
        readonly=True,
    )

    installment_amount = fields.Float(
        string='Installment Amount',
        related='installment_id.amount',
        readonly=True,
    )

    fixed_amount = fields.Float(
        string='Paid Amount',
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()

        loan = self.loan_id
        installment = self.installment_id

        if not installment:
            raise UserError(
                _("Please select an installment.")
            )

        # Selected installment already paid
        if installment.paid:
            raise UserError(
                _("This installment is already paid. "
                  "Please select an unpaid installment.")
            )

        # Amount validation
        if self.fixed_amount <= 0:
            raise UserError(
                _("Paid amount must be greater than zero.")
            )

        if self.fixed_amount > installment.amount:
            raise UserError(
                _("Paid amount cannot be greater than the installment amount.")
            )

        # Remaining amount of selected installment
        remaining_amount = installment.amount - self.fixed_amount

        # Mark selected installment as paid
        installment.write({
            'paid_amount': self.fixed_amount,
        })

        # Get all unpaid installments AFTER selected installment
        next_installments = loan.loan_lines.filtered(
            lambda line: (
                not line.paid
                and line.date > installment.date
            )
        ).sorted(
            key=lambda line: line.date
        )

        # Distribute remaining amount equally
        if remaining_amount > 0:

            if not next_installments:
                raise UserError(
                    _("There are no future unpaid installments "
                      "to distribute the remaining amount.")
                )

            amount_per_installment = (
                remaining_amount / len(next_installments)
            )

            for line in next_installments:
                line.amount += amount_per_installment

        loan._compute_total_amount()

        return {
            'type': 'ir.actions.act_window_close'
        }
