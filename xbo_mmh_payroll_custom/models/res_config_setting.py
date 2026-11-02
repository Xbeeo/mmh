# -*- coding: utf-8 -*-

# from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime, timedelta
from datetime import date
from odoo import api, fields, models, _


class ResCompanyInh(models.Model):
    _inherit = "res.company"

    salary_expense_account_id = fields.Many2one('account.account', string='Salary Expense', tracking=True)
    salaries_payable_account_id = fields.Many2one('account.account', string='Salaries Payable', tracking=True)
    eobi_payable_account_id = fields.Many2one('account.account', string='EOBI Payable', tracking=True)
    social_secuirty_payable_account_id = fields.Many2one('account.account', string='Social Secuirty Payable', tracking=True)
    provident_fund_employee_contribution_payable_account_id = fields.Many2one('account.account', string='Provident Fund Employee Contribution Payable', tracking=True)
    advance_tax_salaries_account_id = fields.Many2one('account.account', string='Advance Tax On Salaries', tracking=True)
    advance_staff_agains_salary_deduction_account_id = fields.Many2one('account.account', string='Advance to Staff against Salary Deduction', tracking=True)
    loan_against_PF_deduction_account_id = fields.Many2one('account.account', string='Loan Against PF Deduction', tracking=True)
    deduction_against_loan_account_id = fields.Many2one('account.account', string='Deduction Against Loan', tracking=True)
    half_day_leave_deduction_account_id = fields.Many2one('account.account', string='Half-Day Leave Deduction', tracking=True)
    excess_leave_deduction_account_id = fields.Many2one('account.account', string='Excess Leave Deduction', tracking=True)

    eobi_employer_contribution_account_id = fields.Many2one('account.account', string='EOBI-Employer Contribution',tracking=True)
    eobi_payable_employer_account_id = fields.Many2one('account.account', string='EOBI Payable Employer',tracking=True)
    provident_fund_expense_account_id = fields.Many2one('account.account', string='Provident Fund Expense',tracking=True)
    provident_fund_employee_contribution_i_payable_account_id = fields.Many2one('account.account',
                                                                              string='Provident Fund Employee Contribution Payable',
                                                                              tracking=True)
    provident_fund_employer_contribution_debit_payable_account_id = fields.Many2one('account.account',
                                                                              string='Provident Fund Employer Contribution Debit Payable',
                                                                              tracking=True)
    provident_fund_employer_contribution_credit_payable_account_id = fields.Many2one('account.account',
                                                                                 string='Provident Fund Employer Contribution Credit Payable',
                                                                                 tracking=True)

    Bank_Cash_account_id = fields.Many2one('account.account',
                                                              string='Bank/Cash Account',
                                                              tracking=True)

class ConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'




    salary_expense_account_id = fields.Many2one(comodel_name='account.account',
                                     related='company_id.salary_expense_account_id',
                                     readonly=False, string="Salary Expense")

    salaries_payable_account_id = fields.Many2one(comodel_name='account.account',
                                     related='company_id.salaries_payable_account_id',
                                     readonly=False, string="Salaries Payable")
    eobi_payable_account_id = fields.Many2one(comodel_name='account.account',
                                                  related='company_id.eobi_payable_account_id',
                                                  readonly=False, string="EOBI Payable")
    social_secuirty_payable_account_id = fields.Many2one(comodel_name='account.account',
                                                  related='company_id.social_secuirty_payable_account_id',
                                                  readonly=False, string="Social Secuirty Payable")
    provident_fund_employee_contribution_payable_account_id = fields.Many2one(comodel_name='account.account',
                                                  related='company_id.provident_fund_employee_contribution_payable_account_id',
                                                  readonly=False, string="Provident Fund Employee Contribution Payable")
    advance_tax_salaries_account_id = fields.Many2one(comodel_name='account.account',
                                                  related='company_id.advance_tax_salaries_account_id',
                                                  readonly=False, string="Advance Tax On Salaries")

    advance_staff_agains_salary_deduction_account_id = fields.Many2one(comodel_name='account.account',
                                                      related='company_id.advance_staff_agains_salary_deduction_account_id',
                                                      readonly=False, string="Advance to Staff against Salary Deduction")

    loan_against_PF_deduction_account_id = fields.Many2one(comodel_name='account.account',
                                                      related='company_id.loan_against_PF_deduction_account_id',
                                                      readonly=False, string="Loan Against PF Deduction")

    deduction_against_loan_account_id = fields.Many2one(comodel_name='account.account',
                                                           related='company_id.deduction_against_loan_account_id',
                                                           readonly=False, string="Deduction Against Loan")



    half_day_leave_deduction_account_id = fields.Many2one(comodel_name='account.account',
                                                      related='company_id.half_day_leave_deduction_account_id',
                                                      readonly=False, string="Half-Day Leave Deduction")

    excess_leave_deduction_account_id = fields.Many2one(comodel_name='account.account',
                                                      related='company_id.excess_leave_deduction_account_id',
                                                      readonly=False, string="Excess Leave Deduction")
    eobi_employer_contribution_account_id = fields.Many2one(comodel_name='account.account',
                                                        related='company_id.eobi_employer_contribution_account_id',
                                                        readonly=False, string="EOBI-Employer Contribution")
    eobi_payable_employer_account_id = fields.Many2one(comodel_name='account.account',
                                                        related='company_id.eobi_payable_employer_account_id',
                                                        readonly=False, string="EOBI Payable Employer")
    provident_fund_expense_account_id = fields.Many2one(comodel_name='account.account',
                                                        related='company_id.provident_fund_expense_account_id',
                                                        readonly=False, string="Provident Fund Expense")
    provident_fund_employee_contribution_i_payable_account_id = fields.Many2one(comodel_name='account.account',
                                                        related='company_id.provident_fund_employee_contribution_i_payable_account_id',
                                                        readonly=False, string="Provident Fund Employee Contribution Payable")
    provident_fund_employer_contribution_debit_payable_account_id = fields.Many2one(comodel_name='account.account',
                                                        related='company_id.provident_fund_employer_contribution_debit_payable_account_id',
                                                        readonly=False, string="Provident Fund Employer Contribution Debit Payable")

    provident_fund_employer_contribution_credit_payable_account_id = fields.Many2one(comodel_name='account.account',
                                                                                    related='company_id.provident_fund_employer_contribution_credit_payable_account_id',
                                                                                    readonly=False,
                                                                                    string="Provident Fund Employer Contribution Credit Payable")

    Bank_Cash_account_id = fields.Many2one(comodel_name='account.account',
                                                        related='company_id.Bank_Cash_account_id',
                                                        readonly=False, string="Bank/Cash Account")



