# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta, date, datetime
from odoo.exceptions import ValidationError


class EmplyeePayslipWizard(models.TransientModel):
    _name = "employee.payslip.wizard"
    _description = "Employee Payslip Wizard"

    date_from = fields.Date(string='Date From', required= True)
    date_to = fields.Date(string='Date To', required= True)
    department_id = fields.Many2one('hr.department', string='Department')
    employee_id = fields.Many2many(comodel_name="hr.employee", string="Employees" ,domain="[('department_id','=',department_id)]")


    def action_print_payslip(self):
        datas = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'employee_id': self.employee_id.ids,
            'department_id': self.department_id.id,
        }
        if self.employee_id:
            employee_ids = self.employee_id.ids

        else:
            if self.department_id:
                employee_ids = self.env['hr.employee'].search([('department_id','=',self.department_id.id)]).ids
            else:
                employee_ids = self.env['hr.employee'].search([]).ids

        pay_slips = self.env['hr.payslip'].search([('date_from', '>=', self.date_from),('date_to', '<=', self.date_to),('employee_id','in',employee_ids),('state','=','done')])


        if pay_slips:

            return self.env.ref('xbo_mmh_payroll_report.action_employee_payslip_report').report_action(self, datas)
        else:
            raise ValidationError('No Record Found!')

class action_employee_payslip_report(models.AbstractModel):
    _name = 'report.xbo_mmh_payroll_report.employee_payslip_report_template'
    _description = 'Employee Payslip Report'

    @api.model
    def _get_report_values(self, docids, data):
        employee_ids = data['employee_id']
        department_id = data['department_id']
        date_from = data['date_from']
        date_to = data['date_to']
        if employee_ids:
            employee_ids = employee_ids
        else:
            if department_id:
                employee_ids = self.env['hr.employee'].search([('department_id', '=', department_id)]).ids
            else:
                employee_ids = self.env['hr.employee'].search([]).ids
        pay_slips = self.env['hr.payslip'].search([('date_from', '>=', date_from),('date_to', '<=', date_to),('employee_id','in',employee_ids),('state','=','done')])
        rule_ids = self.env['hr.payslip.line'].search([('slip_id', 'in', pay_slips.ids)], order='sequence asc').mapped(
            'salary_rule_id')
        rules_list = self.env['hr.payslip.line'].search([('slip_id', 'in', pay_slips.ids)],
                                                        order='sequence asc').mapped('salary_rule_id.id')
        code_names = ['Employee Code', 'Employee Name', 'Department', 'Contact #', 'Joining Date', 'Gross Salary'] + list(
            self.env['hr.salary.rule'].search([('id', 'in', tuple(set(rules_list)))], order='sequence asc').mapped(
                'name'))
        department_wise = pay_slips.read_group([('date_from', '>=', date_from),('date_from', '<=', date_to),('employee_id','in',employee_ids)],
                                               fields=['department_id'], groupby=['department_id'])

        payslips = []
        for emp in department_wise:
            employees = pay_slips.search(emp['__domain'])
            if employees:
                payslips.append({'dept_name': employees[0].employee_id.department_id.name})

            for pay in employees:
                first_contract_obj = self.env['hr.version'].search([('employee_id','=',pay.employee_id.id)], order='id asc', limit=1)
                latest_contract_obj = self.env['hr.version'].search([('employee_id','=',pay.employee_id.id)], order='id asc', limit=1)
                salary_details = {
                    'Employee Code': pay.employee_id.pin,
                    'Employee Name': pay.employee_id.name,
                    'Department': pay.employee_id.department_id.name,
                    'Contact #': pay.employee_id.private_phone,
                    'Joining Date': first_contract_obj.date_start,
                    'Gross Salary': latest_contract_obj.gross_salary,



                    'Employee_wise': True,
                }
                for rule in rule_ids:
                    value = self.env['hr.payslip.line'].search(
                        [('salary_rule_id', '=', rule.id), ('slip_id', '=', pay.id)]).total or 0.0
                    salary_details[rule.name] = "{0:,.1f}".format(value)
                payslips.append(salary_details)

            # departwise sub total
            dept_details = {}
            dept_details['Employee Code'] = 'Dep Total'
            for total in rule_ids:
                value = sum(self.env['hr.payslip.line'].search(
                    [('salary_rule_id', '=', total.id), ('slip_id', 'in', employees.ids)]).mapped('total')) or 0.0
                dept_details[total.name] = "{0:,.1f}".format(value)
            dept_details['departwise'] = True
            payslips.append(dept_details)

        # Grand Total

        dept_grand_total = {}
        dept_grand_total['Employee Code'] = ' Grand Total'
        for total in rule_ids:
            value = sum(self.env['hr.payslip.line'].search(
                [('salary_rule_id', '=', total.id), ('slip_id', 'in', pay_slips.ids)]).mapped('total')) or 0.0
            dept_grand_total[total.name] = "{0:,.1f}".format(value)


        return {
            'docs': payslips,
            'payslips': payslips,
            'code_names': code_names,
            'employees': employees,
            'department_wise': department_wise,
            'pay_slips': pay_slips,
            'dept_grand_total': dept_grand_total,
            'from_date':date_from,
            'to_date': date_to
        }


