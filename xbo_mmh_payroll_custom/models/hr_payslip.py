import babel
from datetime import date, datetime, time,timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    late_count = fields.Integer(string='Late Count')
    shd_count = fields.Integer(string='Shd Count')

    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        """Compute additional inputs for the employee payslip,
        considering active loans.
        :param contract_ids: Contract ID of the current employee.
        :param date_from: Start date of the payslip.
        :param date_to: End date of the payslip.
        :return: List of dictionaries representing additional inputs for
        the payslip."""
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from,
                                                date_to)

        # lo_code = ''
        # for result in res:
        #     if result.get('code') == 'LO':
        #         lo_code = result.get('code')
        #         lo_contract_id = result.get('contract_id')
        #         lo_name = result.get('name')
        #
        # res = [r for r in res if r.get('code') != 'LO']


        employee_id = self.env['hr.version'].browse(
            contract_ids[0].id).employee_id if contract_ids \
            else self.employee_id
        for result in res:
            if result.get('code') == 'LOPF' or result.get('code') == 'LOAS' or result.get('code') == 'LO':
                if result.get('code') == 'LOPF':
                    loan_type = 'pfloan'
                elif result.get('code') == 'LOAS':
                    loan_type = 'advnace'
                else:
                    loan_type = 'loan'

                loan_id = self.env['hr.loan'].search(
                    [('employee_id', '=', employee_id.id), ('state', '=', 'approve'),('loan_type_id.type','=',loan_type)])

                for loan in loan_id:
                    for loan_line in loan.loan_lines:
                        if (date_from <= loan_line.date <= date_to and
                                not loan_line.paid):
                            result['amount'] = (
                                loan_line.paid_amount
                                if loan_line.paid_amount
                                else loan_line.amount
                            )
                            result['loan_line_id'] = loan_line.id
                    # if lo_code == 'LO':
                    #     res.append({
                    #         'code': lo_code,
                    #         'contract_id': lo_contract_id,
                    #         'name': lo_name,
                    #         'amount': loan_line.amount,
                    #         'loan_line_id': loan_line.id,
                    #     })

            if result.get('code') == 'LD':
                late_count = 0
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee_id.id),
                    ('check_in', '>=', date_from),
                    ('check_in', '<=', date_to),
                ])
                if attendances:
                    calendar = employee_id.resource_calendar_id

                    for attendance in attendances:

                        if not attendance.check_in:
                            continue

                        check_in = attendance.check_in

                        # Monday=0, Tuesday=1 ...
                        weekday = str(check_in.weekday())

                        # Employee schedule for current day
                        schedule = calendar.attendance_ids.filtered(
                            lambda a: a.dayofweek == weekday
                        )

                        if not schedule:
                            continue

                        # First shift
                        schedule = schedule[0]

                        # Schedule start time
                        hour_from = schedule.hour_from

                        hour = int(hour_from)
                        minute = int((hour_from % 1) * 60)

                        scheduled_time = check_in.replace(
                            hour=hour,
                            minute=minute,
                            second=0,
                            microsecond=0
                        )

                        # 10 minutes grace time
                        allowed_time = scheduled_time + timedelta(minutes=10)

                        # Late check
                        if check_in + timedelta(hours=5) > allowed_time:
                            late_count += 1

                    payslip_start_date = datetime.strptime(str(date_from), '%Y-%m-%d')
                    payslip_start_month = payslip_start_date.month
                    payslip_start_year = payslip_start_date.year
                    no_of_days = self._numberOfDays(payslip_start_year, payslip_start_month)
                    amount = 0
                    if late_count > 2:
                        amount = ((employee_id.wage / no_of_days) * 0.25) * (late_count-2)
                        self.late_count = late_count - 2
                    result['amount'] = amount

            if result.get('code') == 'SHD':
                late_count = 0
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee_id.id),
                    ('check_in', '>=', date_from),
                    ('check_in', '<=', date_to),
                ])
                if attendances:
                    for attendance in attendances:
                        if attendance.worked_hours < 6.0:
                            late_count += 1

                    payslip_start_date = datetime.strptime(str(date_from), '%Y-%m-%d')
                    payslip_start_month = payslip_start_date.month
                    payslip_start_year = payslip_start_date.year
                    no_of_days = self._numberOfDays(payslip_start_year, payslip_start_month)
                    amount = ((employee_id.wage / no_of_days) * 0.25) * (late_count)
                    self.shd_count = late_count
                    result['amount'] = amount

        return res

    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',store=True)

    journal_entries_count = fields.Integer(string='Project Count', compute='_compute_entries_count')

    def _compute_entries_count(self):
        for x in self:
            move_obj = self.env['account.move'].search([('payslip_id', '=', x.id)])
            x.journal_entries_count = len(move_obj)

    def action_view_journal_entries(self):
        self.ensure_one()
        move_obj = self.env['account.move'].search([('payslip_id', '=', self.id)])

        action = {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', move_obj.ids)],
        }

        if len(move_obj) == 1:
            action.update({'views': [(False, 'form')], 'res_id': move_obj.id})
        return action



    def action_print_report(self):
        return self.env.ref('om_hr_payroll.action_report_payslip').report_action(self)


    def custom_action_payslip_done(self):
        """ Compute the loan amount and remaining amount while confirming
                    the payslip"""

        self.compute_sheet()

        for slip in self:
            net_line = slip.details_by_salary_rule_category.filtered(
                lambda l: l.code == 'NET'
            )

            if net_line and net_line.total < 0:
                raise ValidationError(
                    _("The net salary of employee %s cannot be negative. "
                      "Please review the deductions before confirming the payslip.")
                    % slip.employee_id.name
                )

        pf_obj = self.env['provident.fund'].search([('payslip_id', '=', self.id)])
        if pf_obj:
            pf_obj.state = 'done'

        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_total_amount()

        self.write({'state': 'done'})

        for slip in self:
            line_ids1 = []
            line_ids2 = []
            line_ids3 = []
            line_ids4 = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            currency = slip.company_id.currency_id

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
                'employee_id': slip.employee_id.id,
                'payslip_id' : slip.id
            }

            line = slip.details_by_salary_rule_category.filtered(lambda l:l.code == 'GROSS')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.salary_expense_account_id:
                    raise UserError(_('Missing Salary Expense Account in General Setting'))
                debit_account_id = slip.company_id.salary_expense_account_id.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_distribution': {line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(debit_line)


            line = slip.details_by_salary_rule_category.filtered(lambda l:l.code == 'NET')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.salaries_payable_account_id:
                    raise UserError(_('Missing Salaries Payable Account in General Setting'))
                credit_account_id = slip.company_id.salaries_payable_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)



            line = slip.details_by_salary_rule_category.filtered(lambda l:l.code == 'EOBI')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.eobi_payable_account_id:
                    raise UserError(_('Missing EOBI Payable Account in General Setting'))
                credit_account_id = slip.company_id.eobi_payable_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)


            line = slip.details_by_salary_rule_category.filtered(lambda l:l.code == 'SS')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.social_secuirty_payable_account_id:
                    raise UserError(_('Missing Social Secuirty Payable Account in General Setting'))
                credit_account_id = slip.company_id.social_secuirty_payable_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'PF')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.provident_fund_employee_contribution_payable_account_id:
                    raise UserError(_('Missing Provident Fund Employee Contribution Payable Account in General Setting'))
                credit_account_id = slip.company_id.provident_fund_employee_contribution_payable_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)
            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'WHT')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.advance_tax_salaries_account_id:
                    raise UserError(
                        _('Missing Advance Tax On Salaries Account in General Setting'))
                credit_account_id = slip.company_id.advance_tax_salaries_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'LOAS')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.advance_staff_agains_salary_deduction_account_id:
                    raise UserError(
                        _('Missing Advance to Staff against Salary Deduction Account in General Setting'))
                credit_account_id = slip.company_id.advance_staff_agains_salary_deduction_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'LOPF')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.loan_against_PF_deduction_account_id:
                    raise UserError(
                        _('Missing Loan Against PF Deduction Account in General Setting'))
                credit_account_id = slip.company_id.loan_against_PF_deduction_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'LO')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.deduction_against_loan_account_id:
                    raise UserError(
                        _('Missing Deduction Against Loan Account in General Setting'))
                credit_account_id = slip.company_id.deduction_against_loan_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)


            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'LD')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.half_day_leave_deduction_account_id:
                    raise UserError(
                        _('Missing Half-Day Leave Deduction Account in General Setting'))
                credit_account_id = slip.company_id.half_day_leave_deduction_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'SHD')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.excess_leave_deduction_account_id:
                    raise UserError(
                        _('Missing Excess Leave Deduction Account in General Setting'))
                credit_account_id = slip.company_id.excess_leave_deduction_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids1.append(credit_line)


            move_dict['line_ids'] = line_ids1
            move = self.env['account.move'].create(move_dict)
            slip.write({'date': date})

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict_2 = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
                'employee_id': slip.employee_id.id,
                'payslip_id': slip.id
            }

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'EOBI')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            amount = 5 * amount
            if not currency.is_zero(amount):
                if not slip.company_id.eobi_employer_contribution_account_id:
                    raise UserError(_('Missing EOBI-Employer Contribution Account in General Setting'))
                debit_account_id = slip.company_id.eobi_employer_contribution_account_id.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids2.append(debit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'EOBI')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            amount = 5 * amount
            if not currency.is_zero(amount):
                if not slip.company_id.eobi_payable_employer_account_id:
                    raise UserError(_('Missing EOBI Payable Employer Account in General Setting'))
                credit_account_id = slip.company_id.eobi_payable_employer_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids2.append(credit_line)

            move_dict_2['line_ids'] = line_ids2
            # move = self.env['account.move'].create(move_dict_2)
            # slip.write({'date': date})

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict_3 = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
                'employee_id': slip.employee_id.id,
                'payslip_id': slip.id
            }

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'PF')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.provident_fund_expense_account_id:
                    raise UserError(_('Missing Provident Fund Expense Account in General Setting'))
                debit_account_id = slip.company_id.provident_fund_expense_account_id.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids3.append(debit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'PF')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))

            if not currency.is_zero(amount):
                if not slip.company_id.provident_fund_employer_contribution_credit_payable_account_id:
                    raise UserError(_('Missing Provident Fund Employer Contribution Credit Payable Account in General Setting'))
                credit_account_id = slip.company_id.provident_fund_employer_contribution_credit_payable_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids3.append(credit_line)

            move_dict_3['line_ids'] = line_ids3
            # move = self.env['account.move'].create(move_dict_3)
            # slip.write({'date': date})

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict_4 = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
                'employee_id': slip.employee_id.id,
                'payslip_id': slip.id
            }

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'PF')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.provident_fund_employee_contribution_i_payable_account_id:
                    raise UserError(_('Missing Provident Fund Employee Contribution Payable Account in General Setting'))
                debit_account_id = slip.company_id.provident_fund_employee_contribution_i_payable_account_id.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids4.append(debit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'PF')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            if not currency.is_zero(amount):
                if not slip.company_id.provident_fund_employer_contribution_debit_payable_account_id:
                    raise UserError(
                        _('Missing Provident Fund Employer Contribution Debit Payable Account in General Setting'))
                debit_account_id = slip.company_id.provident_fund_employer_contribution_debit_payable_account_id.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=False),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids4.append(debit_line)

            line = slip.details_by_salary_rule_category.filtered(lambda l: l.code == 'PF')
            amount = abs(currency.round(slip.credit_note and -line.total or line.total))
            amount = 2 * amount
            if not currency.is_zero(amount):
                if not slip.company_id.Bank_Cash_account_id:
                    raise UserError(
                        _('Missing Bank/Cash Account Account in General Setting'))
                credit_account_id = slip.company_id.Bank_Cash_account_id.id

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': line._get_partner_id(credit_account=True),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                        'analytic_distribution': {
                            line.salary_rule_id.analytic_account_id.id: 100} if line.salary_rule_id.analytic_account_id else {},
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids4.append(credit_line)

            move_dict_4['line_ids'] = line_ids4
            # move = self.env['account.move'].create(move_dict_4)
            # slip.write({'date': date})


        return








    def action_payslip_done(self):
        """ Compute the loan amount and remaining amount while confirming
            the payslip"""
        print()
        # pf_obj = self.env['provident.fund'].search([('payslip_id','=',self.id)])
        # if pf_obj:
        #     pf_obj.state = 'done'
        #
        # for line in self.input_line_ids:
        #     if line.loan_line_id:
        #         line.loan_line_id.paid = True
        #         line.loan_line_id.loan_id._compute_total_amount()
        # return super(HrPayslip, self).action_payslip_done()

    def action_payslip_cancel(self):
        pf_obj = self.env['provident.fund'].search([('payslip_id', '=', self.id)])
        if pf_obj:
            pf_obj.state = 'cancel'
        return super(HrPayslip, self).action_payslip_cancel()


    def _numberOfDays(self, y, m):
        leap = 0
        if y % 400 == 0:
            leap = 1
        elif y % 100 == 0:
            leap = 0
        elif y % 4 == 0:
            leap = 1
        if m == 2:
            return 28 + leap
        list = [1, 3, 5, 7, 8, 10, 12]
        if m in list:
            return 31
        return 30


    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and \
                                                          localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                        SELECT sum(amount) as sum
                        FROM hr_payslip as hp, hr_payslip_input as pi
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                        SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                        FROM hr_payslip as hp, hr_payslip_worked_days as pi
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                                FROM hr_payslip as hp, hr_payslip_line as pl
                                WHERE hp.employee_id = %s AND hp.state = 'done'
                                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.version'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    if rule.check_box_nod:
                        day_from = datetime.combine(fields.Date.from_string(payslip.date_from), time.min)
                        day_to = datetime.combine(fields.Date.from_string(payslip.date_to), time.max)
                        work_data = contract.employee_id._get_work_days_data(
                            day_from,
                            day_to,
                            calendar=contract.resource_calendar_id,
                            compute_leaves=False,
                        )
                        payslip_start_date = datetime.strptime(str(payslip.date_from), '%Y-%m-%d')
                        payslip_start_month = payslip_start_date.month
                        payslip_start_year = payslip_start_date.year
                        no_of_days = self._numberOfDays(payslip_start_year, payslip_start_month)

                        amount = (amount / no_of_days) * work_data['days']

                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = contract.company_id.currency_id.round(amount * qty * rate / 100.0)
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'version_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return list(result_dict.values())


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Batches'



    def custom_done_payslip_run(self):
        for line in self.slip_ids:
            line.custom_action_payslip_done()
        return self.write({'state': 'done'})