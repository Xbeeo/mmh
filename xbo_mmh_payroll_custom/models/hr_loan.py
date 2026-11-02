# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    """ Model for managing loan requests."""
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        """ Function used to pass employee corresponding to current login user
            as default employee while creating new loan request
            :param field_list : Fields and values for the model hr.loan"""
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            user_id = result['user_id']
        else:
            user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search(
            [('user_id', '=', user_id)], limit=1).id
        return result

    name = fields.Char(string="Loan Name", copy=False, readonly=True, default=lambda s: s.env._('New'),
                       help="Name of the loan", tracking=True)
    date = fields.Date(string="Date", default=fields.Date.today(),
                       readonly=True, help="Date of the loan request" , tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  required=True, help="Employee Name" , tracking=True)
    loan_type_id = fields.Many2one('loan.type', string="Loan Type",
                                  required=True, help="Loan Type" , tracking=True)
    type_code = fields.Selection(string="Loan Type Code", related='loan_type_id.type', store=True)
    department_id = fields.Many2one('hr.department',
                                    related="employee_id.department_id",
                                    readonly=True,
                                    string="Department",
                                    help="The department to which the "
                                         "employee belongs." , tracking=True)
    installment = fields.Integer(string="No Of Installments", default=1,
                                 help="Number of installments" , tracking=True)
    payment_date = fields.Date(string="Payment Start Date", required=True,
                               default=fields.Date.today(),
                               help="Date of the payment" , tracking=True)
    loan_lines = fields.One2many('hr.loan.line', 'loan_id',
                                 string="Loan Line",
                                 help="Details of installment lines "
                                      "associated with the loan.",
                                 index=True)
    by_pass_validation = fields.Boolean(string='By Pass Further Loan Validation!',default=False, tracking=True)

    # provident_fund_lines = fields.One2many('provident.fund.line', 'loan_id',
    #                              string="Loan Line",
    #                              help="Details of installment lines "
    #                                   "associated with the Provident Fund loan.",
    #                              index=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Company",
                                 default=lambda self: self.env.user.company_id, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, help="Currency",
                                  default=lambda self: self.env.user.
                                  company_id.currency_id, tracking=True)
    job_position_id = fields.Many2one('hr.job',
                                   related="employee_id.job_id",
                                   readonly=True, string="Job Position",
                                   help="Job position of the employee")
    loan_amount = fields.Float(string="Loan Amount", required=True,
                               help="Loan amount", tracking=True)
    total_amount = fields.Float(string="Total Amount", store=True,
                                readonly=True, compute='_compute_total_amount',
                                help="The total amount of the loan")
    balance_amount = fields.Float(string="Balance Amount", store=True,
                                  compute='_compute_total_amount',
                                  help="""The remaining balance amount of the 
                                  loan after deducting 
                                  the total paid amount.""")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True,
                                     compute='_compute_total_amount',
                                     help="The total amount that has been "
                                          "paid towards the loan.")

    total_pf_amount = fields.Float(string="Total PF Amount", store=True,
                                     compute='_compute_total_pf_amount',)


    state = fields.Selection(
        [('draft', 'Draft'), ('waiting_approval_1', 'Submitted'),
         ('approve', 'Approved'), ('refuse', 'Refused'), ('cancel', 'Cancelled'),
         ], string="State", default='draft', help="The current state of the "
                                                  "loan request.", copy=False, tracking=True)


    @api.onchange('loan_amount')
    def check_loan_amount(self):
        if self.type_code == 'pfloan':
            if self.loan_amount > self.total_pf_amount:
                raise ValidationError('Loan amount should not be greater then the PF amount!')


    @api.depends('loan_type_id','employee_id')
    def _compute_total_pf_amount(self):
        for x in self:
            total_pf = 0.0
            if x.type_code == 'pfloan':
                total_period_sum = sum(self.env['provident.fund'].search([
                    ('employee_id', '=', x.employee_id.id),('state','=','done')
                ]).mapped('total_PF_period'))
                x.total_pf_amount = total_period_sum

            else:
                x.total_pf_amount = total_pf

    def _compute_total_amount(self):
        """Compute total loan amount, balance amount and total paid amount."""
        for loan in self:
            total_paid = sum(
                line.paid_amount
                for line in loan.loan_lines
                if line.paid
            )

            loan.total_amount = loan.loan_amount
            loan.total_paid_amount = total_paid
            loan.balance_amount = loan.loan_amount - total_paid

    def action_fixed_installment(self):
        self.ensure_one()

        installment = self.loan_lines.filtered(
            lambda line: not line.paid
        ).sorted(
            key=lambda line: line.date
        )[:1]

        if not installment:
            raise UserError(
                _("There is no unpaid installment available.")
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Fixed Installment'),
            'res_model': 'hr.loan.fixed.installment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_loan_id': self.id,
                'default_installment_id': installment.id,
                'default_payment_date': installment.date,
                'default_fixed_amount': installment.amount,
            },
        }

    # @api.model
    # def create(self, values):
    #     """ Check whether any pending loan is for the employee and calculate
    #         the sequence
    #         :param values : Dictionary which contain fields and values"""
    #
    #     loan_count = self.env['hr.loan'].search_count(
    #         [('employee_id', '=', values['employee_id']),
    #          ('state', '=', 'approve'),
    #          ('balance_amount', '!=', 0)])
    #     if loan_count and not values['by_pass_validation']:
    #         raise ValidationError(
    #             _("The Employee has already a pending installment"))
    #
    #     else:
    #         values['name'] = self.env['ir.sequence'].next_by_code('hr.loan.seq') or ' '
    #         return super(HrLoan, self).create(values)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            loan_count = self.env['hr.loan'].search_count(
                [('employee_id', '=', vals['employee_id']),
                 ('state', '=', 'approve'),
                 ('balance_amount', '!=', 0)])
            if loan_count and not vals['by_pass_validation']:
                raise ValidationError(
                    _("The Employee has already a pending installment"))

            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.seq') or _('New')

        return super().create(vals_list)

    def action_compute_installment(self):
        """This automatically create the installment the employee need to pay to
            company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_total_amount()



        return True

    def action_refuse(self):
        """ Function to reject loan request"""
        return self.write({'state': 'refuse'})

    def action_submit(self):
        if self.employee_id.contract_date_start:
            if self.date < (self.employee_id.contract_date_start + relativedelta(years=1)):
                raise ValidationError(
                    _("There must be at least a 1-year gap between the request date and contract Start date.")
                )
        else:
            raise ValidationError(_("Please add emplyee contract date"))
        if self.loan_type_id.type == 'loan' and  self.loan_amount > (self.employee_id.wage * 3):
            raise ValidationError(_("The loan amount not exceed the employee's three-month salary."))

        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        """ Function to cancel loan request"""
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        """ Function to cancel loan request"""
        self.write({'state': 'draft'})

    def action_approve(self):
        """ Function to approve loan request"""
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

    def unlink(self):
        """ Function which restrict the deletion of approved or submitted
                loan request"""
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(_(
                    'You cannot delete a loan which is not in draft '
                    'or cancelled state'))
        return super(HrLoan, self).unlink()

