# -*- coding: utf-8 -*-
######################################################################################
#
#    Keffah Solutions the Est. Information technology and Communication  Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Keffah Solutions the Est. Information technology and Communication Pvt. Ltd
#    (<https://www.kascco.sa>).
#    Author: Keffah Solutions the Est. Information technology and Communication Pvt. Ltd (Contact : itcs@kascco.sa)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
import base64
import xml.etree.ElementTree as ET
import odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


def _export_xml_id(self):
    """ Return a valid xml_id for the record ``self``. """
    if not self._is_an_ordinary_table():
        raise Exception(
            "You can not export the column ID of model %s, because the "
            "table %s is not an ordinary table."
            % (self._name, self._table))
    ir_model_data = self.sudo().env['ir.model.data']
    data = ir_model_data.search([('model', '=', self._name),
                                 ('res_id', '=', self.id)])
    if data:
        if data[0].module:
            return '%s.%s' % (data[0].module, data[0].name)
        else:
            return data[0].name
    else:
        postfix = 0
        name = '%s_%s' % (self._table, self.id)
        while ir_model_data.search([('module', '=', '__export__'),
                                    ('name', '=', name)]):
            postfix += 1
            name = '%s_%s_%s' % (self._table, self.id, postfix)
        ir_model_data.create({
            'model': self._name,
            'res_id': self.id,
            'module': '__export__',
            'name': name,
        })
        return '__export__.' + name


class Approval(models.Model):
    """This class is creating the approval forms and it's functions"""
    _name = 'dynamic.approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Dynamic Multi Approval'

    name = fields.Char(string='Approval Number', readonly=True,
                       required=True, copy=False, index=True, tracking=True,
                       default=lambda self: _('New'))
    approval_name = fields.Char(string="Approval Name", required=True,
                                help='Name given for the created approval')
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               index=True,
                               ondelete='cascade',
                               help='Choose a model to create approval upon it'
                               )
    state_domain = fields.Many2many('ir.model.fields.selection',
                                    'state_domain')
    model_states = fields.Many2many('ir.model.fields.selection',
                                    string='State', required=False,
                                    help='Sates of the chosed model',
                                    domain="[('id', 'in', state_domain)]")
    record_ids = fields.Many2many('model.data', required=True,
                                  string='State', help='Choose a state to '
                                                       'create approval '
                                                       'request upon that '
                                                       'state',
                                  domain="[('save', '!=', True),"
                                         "('stage_id', '=', True)]"
                                  )

    list_view_domain_ids = fields.Many2many('ir.ui.view',
                                            'list_view_domain')
    search_view_domain_ids = fields.Many2many('ir.ui.view',
                                              relation='search_view_domain_ids')
    category_id = fields.Many2one('res.groups.privilege',
                                  string="Category",
                                  help='Category of selected model',
                                  required=True)
    action_id = fields.Many2many("ir.actions.act_window",
                                 string="Actions Window", required=True,
                                 help='Actions of selected model',
                                 domain="[('res_model', '=', model_name)]")
    external_id = fields.Text(string="External Id",
                              help='Id of selected action',
                              compute="_compute_external_id", readonly=True)
    group_id = fields.Many2one('res.groups')
    view_id = fields.Many2one('ir.ui.view')
    company_id = fields.Many2many('res.company', string='Company',
                                  required=True)
    remove_reports = fields.Boolean(string="Remove Reports")

    add_approval_status_to_list = fields.Boolean(string="Add Approval Status"
                                                        " To Tree View",
                                                 help='Enable to add Approval '
                                                      'Status to Tree View')
    list_view_id = fields.Many2many('ir.ui.view')
    list_view_name = fields.Many2many('ir.ui.view',
                                      'x_list_view',
                                      'x_list_view_relation',
                                      string='Tree View Name',
                                      help='Tree view names of current model',
                                      domain="[('id', 'in', "
                                             "list_view_domain_ids)]")
    list_view_inherit_id = fields.Text(string="Tree View External Id",
                                       help='Id of selected list views',
                                       compute="_compute_list_external_id",
                                       readonly=True)

    add_filter = fields.Boolean(string="Add Filter",
                                help='Enable to add filter')
    search_view_id = fields.Many2many('ir.ui.view',
                                      'x_search_view',
                                      'x_search_view_relation')
    search_view_name = fields.Many2many('ir.ui.view',
                                        'x_search_view_name',
                                        'x_search_view_name_relation',
                                        domain="[('id', 'in', "
                                               "search_view_domain_ids)]")
    search_view_inherit_id = fields.Text(string="Search View External Id",
                                         compute="_compute_search_external_id")
    model_name = fields.Char(string='Model name', help='Model name of '
                                                       'current model')

    enable_time_limit = fields.Boolean(string="Enable Timer",
                                       help="This will activate the Time "
                                            "limit for the approvers")
    timer = fields.Float(string="Time Limit", help='timer')
    timer_type = fields.Selection([('hours', 'Hours')],
                                  string='Timer Type', default='hours',
                                  help='Time type',
                                  readonly=True)
    user_ids = fields.Many2many('res.users', string='Authority',
                                help='Authority of delay timer check',
                                tracking=True)
    individual_time_limit = fields.Boolean(string="Individual Time Limit",
                                           help="This will activate the Time "
                                                "limit can set individualy")
    delay_time = fields.Integer(default=1, help="Check delay every x.")
    delay_type = fields.Selection([('minutes', 'Minutes'),
                                   ('hours', 'Hours'),
                                   ('days', 'Days'),
                                   ('weeks', 'Weeks'),
                                   ('months', 'Months')],
                                  string='Delay Type',
                                  help='Delay Type', default='hours')
    is_reminder = fields.Boolean(string="Reminder Mail", default=False,
                                 help='Enable to send remainder mail')
    users = fields.One2many('approver.line',
                            'approver_id', string='Approvers')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('multi_state_activated', 'Multi State Activated'),
        ('old', 'Apply to Old Records'),
        ('update', 'Update'),
        ('apply', 'Approvers List Updated'),
        ('cancel', 'Refused'),
        ('fail', 'Failed')
    ], string='Status', index=True, tracking=True,
        copy=False, default='draft',
        required=True, help='Approval State')

    """````````````````````````````````````````````````````````````````"""
    compute_approve = fields.Many2one('ir.model.fields')
    compute_one = fields.Many2one('ir.model.fields')
    """````````````````````````````````````````````````````````````````"""
    custom_field_id = fields.Many2one('ir.model.fields')
    multi_state_field_id = fields.Many2one('ir.model.fields')
    fully_approved_field_id = fields.Many2one('ir.model.fields')
    need_to_approve_id = fields.Many2one('ir.model.fields')
    reminder_mail = fields.Many2one('ir.model.fields')
    parallel_approval_duration_id = fields.Many2one('ir.model.fields')
    multi_approver_status_checker_id = fields.Many2one('ir.model.fields')
    header_status_checker = fields.Many2one('ir.model.fields')
    email_status_checker_id = fields.Many2one('ir.model.fields')
    check_old_records_id = fields.Many2one('ir.model.fields')

    approve_state_id = fields.Many2one('ir.model.fields')
    reject_reason_id = fields.Many2one('ir.model.fields')

    report_action_ids = fields.Many2many('ir.actions.report',
                                         string='Report Actions')
    automation_action_id_two = fields.Many2one('base.automation')
    automation_action_id_three = fields.Many2one('base.automation')
    approves_automation_action_id = fields.Many2one('base.automation')
    state_specific_approves_automation_id = fields.Many2one('base.automation')
    automation_action_id = fields.Many2one('base.automation')
    email_template_id = fields.Many2one('mail.template')
    check_approval_delay = fields.Many2one('ir.cron')

    approve_server_action_id = fields.Many2one('ir.actions.server')
    reject_server_action_id = fields.Many2one('ir.actions.server')
    re_send_server_action_id = fields.Many2one('ir.actions.server')
    email_template_server_action_id = fields.Many2one('ir.actions.server')
    multiple_server_action_id = fields.Many2one('ir.actions.server')

    approver_ids = fields.Many2one('ir.model.fields')
    approval_model = fields.Many2one('ir.model.fields')
    approval_id = fields.Many2one('ir.model.fields')
    state_count = fields.Boolean(compute='compute_state_count',
                                 help='To determine the state count of current '
                                      'created approval request')
    check_states_type = fields.Boolean(default=False, help="To check weather "
                                                           "the selected "
                                                           "model contains "
                                                           "state field in it")
    list_field_id = fields.Many2one('model.data',
                                    domain="[('save', '!=', True),"
                                           "('is_field', '=', True)]",
                                    string='Tree Field', help='Choose a field '
                                                              'to create the '
                                                              'approval '
                                                              'status '
                                                              'after/before '
                                                              'this field'
                                    )
    field_position = fields.Selection(selection=[
        ('after', 'After'),
        ('before', 'Before')
    ], default='after', string='Field Position', required=True,
        help="choose the position "
             "attribute for the "
             "approval state in list "
             "view")
    is_enabled = fields.Boolean(string="Visible In Tree View", default=True,
                                help="By default enabled and visible in list "
                                     "view if disabled optional hide in list "
                                     "view")
    approval_method = fields.Selection(selection=[
        ('sequence', 'Sequential Approval'),
        ('parallel', 'Parallel Approval'),
        ('hierarchy', 'Employee Hierarchy Approval')
    ], string='Approval Method', default='sequence', required=True,
        help='Choose the approval type')
    multi_state_enabled = fields.Boolean(string='Is Multi state',
                                         help='whether multi state is enabled')
    apply_old_records = fields.Boolean(string='Is Old record active',
                                       help='whether applied to old record')
    state_specific_approval = fields.Boolean(string='State Specific Approval',
                                             help='If enabled approvals can be '
                                                  'set approves per state')

    # selection_states = fields.Many2many('ir.model.fields.selection',
    #                                     'states_link')
    # compute='_compute_selection_states')

    # @api.depends('users')
    # def _compute_selection_states(self):
    #     """Compute function to compute values to field selection state"""
    #     self.selection_states = [fields.Command.clear()]
    #     for rec in self.users:
    #         if rec.model_states.id:
    #             self.selection_states = [
    #                 fields.Command.link(rec.model_states.id)]

    @api.onchange('state_specific_approval')
    def _onchange_state_specific_approval(self):
        """Function called onchange of state_specific_approval to clears the
        field users and selection states"""
        self.users = [fields.Command.clear()]
        # self.selection_states = [fields.Command.clear()]

    @api.onchange('enable_time_limit')
    def _onchange_enable_time_limit(self):
        """Function called each time when enable_time_limit field changes"""
        if not self.enable_time_limit:
            self.timer = 00.00
            self.individual_time_limit = False
            self.user_ids = [fields.Command.clear()]

    @api.onchange('approval_method')
    def _onchange_approval_method(self):
        """Clear the Users lines if the approval method is hierarchy"""
        if self.approval_method == 'hierarchy':
            self.users = [(5, 0, 0)]
        if self.state_specific_approval:
            self.state_specific_approval = False

    @api.onchange('model_id')
    def view_model_fields(self):
        """Function called each time when model_id changes"""
        if self.model_id and self.list_view_domain_ids:
            for rec in self.list_view_domain_ids:
                if rec._origin.xml_id:
                    kk = self.env.ref(rec._origin.xml_id)
                    root = ET.fromstring(kk.arch)
                    fields = root.findall(".//field")
                    for field in fields:
                        self.env['model.data'].create({
                            'rec_name': field.get('name'),
                            'is_field': True
                        })

    @api.onchange('users')
    def _onchange_users_type(self):
        """Function check if approval type manager is already chosen"""
        if self.users.mapped('approval_type').count('manager') > 1:
            raise UserError(_("Manager approval is already Chosen"))

    @api.depends('model_states')
    def compute_state_count(self):
        """To check weather to enable multi state approval"""
        for rec in self:
            stage_id = rec.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                if rec.record_ids:
                    if len(self.record_ids) > 1:
                        rec.state_count = True
                    else:
                        rec.state_count = False
                else:
                    rec.state_count = False
            else:
                if rec.model_states:
                    if len(rec.model_states.ids) > 1:
                        rec.state_count = True
                    else:
                        rec.state_count = False
                else:
                    rec.state_count = False

    @api.model_create_multi
    def create(self, vals_list):
        """Create approval records with sequence numbers."""
        for vals in vals_list:
            if vals.get('sequence', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dynamic.approval'
                ) or _('New')

        return super(Approval, self).create(vals_list)

    @api.depends('action_id')
    def _compute_external_id(self):
        """Function compute the external id"""
        for rec in self:
            rec.external_id = str(self.action_id.mapped('xml_id'))

    @api.depends('list_view_name')
    def _compute_list_external_id(self):
        """Function to compute the list_view_inherit_id"""
        for rec in self:
            rec.list_view_inherit_id = str(
                rec.list_view_name._origin.mapped('xml_id'))

    @api.depends('search_view_name')
    def _compute_search_external_id(self):
        """Function to compute the search_view_inherit_id"""
        for rec in self:
            rec.search_view_inherit_id = str(
                rec.search_view_name._origin.mapped('xml_id'))

    @api.onchange('approval_name')
    def filter_model(self):
        """This onchange() will filter state field contain models"""
        stage_id_field_contain_models = self.env['ir.model.fields'].search(
            [('ttype', '=', 'many2one'), ('name', '=', 'stage_id')]).mapped(
            'model_id').ids
        state_field_contain_models = self.env['ir.model.fields'].search(
            [('ttype', '=', 'selection'), ('name', '=', 'state')]).mapped(
            'model_id').ids
        model_ids = stage_id_field_contain_models + state_field_contain_models
        return {'domain': {'model_id': [('id', 'in', model_ids)
                                        ]}}

    @api.onchange('model_id')
    def onchange_model_id(self):
        """This Onchange function will list the selected model state values,
        action_id and list view name"""
        self.list_view_domain_ids = [(6, 0, [])]
        self.search_view_domain_ids = [(6, 0, [])]
        self.action_id = [(6, 0, [])]
        self.record_ids = [(6, 0, [])]
        self.model_states = [(6, 0, [])]
        records = self.env['model.data'].search([
            ('save', '!=', True)])
        model = self.model_id
        if records:
            for rec in records:
                rec.unlink()
            self.model_id = model.id

        self.model_name = self.model_id.model
        if self.model_name == "account.move":
            self.list_view_domain_ids = self.model_id.view_ids.filtered(
                lambda l: l.type == 'list')
        else:
            self.list_view_domain_ids = self.model_id.view_ids.filtered(
                lambda l: l.type == 'list' and not l.inherit_id)
        self.search_view_domain_ids = self.model_id.view_ids.filtered(
            lambda l: l.type == 'search')

        if self.model_id.field_id.filtered(lambda l: l.name == 'stage_id'):
            self.check_states_type = True
            if self.model_id.name == 'Task':
                fields = self.env['ir.model.fields'].search([
                    ('model_id', '=', self.model_id.id),
                    ('name', '=', 'stage_id')])
                print(fields.relation)
                values = self.env[fields.relation].search([
                    ('project_ids', '!=', False)])
                for record in values:
                    self.env['model.data'].create({
                        'rec_name': record.name,
                        'rec_id': str(record.id),
                        'stage_id': True
                    })
            else:
                fields = self.env['ir.model.fields'].search([
                    ('model_id', '=', self.model_id.id),
                    ('name', '=', 'stage_id')])
                values = self.env[fields.relation].search([])
                for record in values:
                    self.env['model.data'].create({
                        'rec_name': record.name,
                        'rec_id': str(record.id),
                        'stage_id': True
                    })
        elif self.model_id.field_id.filtered(
                lambda l: l.name == 'state').selection_ids.mapped('id'):
            self.check_states_type = False
            self.state_domain = self.model_id.field_id.filtered(
                lambda l: l.name == 'state').selection_ids.mapped('id')

    def create_button(self):
        """This function will create the approval needed field,Button functions
        and it will inherit and create new
        view in corresponding model"""
        company_id = self.env.company
        if (not company_id.phone and not company_id.email
                and not company_id.website):
            raise UserError(_("Please set the Company Phone,Email and Website"))
        if not company_id.phone:
            raise UserError(_("Please set the Company Phone "))
        if not company_id.email:
            raise UserError(_("Please set the Company Email "))
        if not company_id.website:
            raise UserError(_("Please set the Company Website "))
        stage_id = self.model_id.field_id.filtered(
            lambda l: l.name == 'stage_id')
        if stage_id:
            xml = self.env['ir.ui.view'].search([
                ('model', '=', self.model_id.model),
                ('type', '=', 'form')], limit=1)
            inherit_id = xml
        else:
            xml_id = self.model_id.view_ids.filtered(
                lambda l: not l.inherit_id and l.type == 'form')[0].xml_id
            inherit_id = self.env.ref(xml_id)
        group_obj = self.env['res.groups']
        inherit_name = inherit_id.name + ".dynamic.approval"

        approve_action_name = self.model_id.name + ' Approve Action'
        reject_action_name = self.model_id.name + ' Reject Action'
        re_send_action_name = self.model_id.name + ' Resend Action'
        if not self.compute_one:
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                self.compute_one = self.env['ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_compute_one',
                    'field_description': 'X Compute One',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': True,
                    'depends': 'stage_id',
                    'compute': """
for record in self:
    if record.x_compute_one:
        record.write({'x_compute_one': False})
    else:
        record.write({'x_compute_one': True})
        """
                })
            else:
                self.compute_one = self.env['ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_compute_one',
                    'field_description': 'X Compute One',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': True,
                    'depends': 'state',
                    'compute': """
for record in self:
    if record.x_compute_one:
        record.write({'x_compute_one': False})
    else:
        record.write({'x_compute_one': True})
        """
                })
        if not self.compute_approve:
            self.compute_approve = self.env['ir.model.fields'].sudo().create({
                'ttype': 'boolean',
                'name': 'x_compute',
                'field_description': 'X Compute',
                'model_id': self.model_id.id})
        if not self.custom_field_id:
            self.custom_field_id = self.env['ir.model.fields'].sudo().create({
                'ttype': 'boolean',
                'name': 'x_approve',
                'field_description': 'Approve',
                'readonly': 'True',
                'model_id': self.model_id.id})
        if not self.need_to_approve_id:
            self.need_to_approve_id = self.env['ir.model.fields'].sudo().create(
                {
                    'ttype': 'boolean',
                    'name': 'x_need_to_approve',
                    'field_description': 'Need To Approve',
                    # 'readonly': 'True',
                    'model_id': self.model_id.id})
        if not self.parallel_approval_duration_id:
            self.parallel_approval_duration_id = self.env[
                'ir.model.fields'].sudo().create({
                'ttype': 'boolean',
                'name': 'x_check_parllel_approval',
                'field_description': 'Check Parallel Approval Duration',
                'readonly': 'True',
                'model_id': self.model_id.id})
        if not self.reminder_mail:
            self.reminder_mail = self.env['ir.model.fields'].sudo().create({
                'ttype': 'boolean',
                'name': 'x_reminder_mail',
                'field_description': 'Check Delay Mail Reminder ',
                'readonly': 'True',
                'model_id': self.model_id.id})

        if not self.approve_state_id:
            self.approve_state_id = self.env['ir.model.fields'].sudo().create({
                'ttype': 'selection',
                'name': 'x_approve_state',
                'field_description': 'Approval Status',
                'model_id': self.model_id.id})
            self.env['ir.model.fields.selection'].sudo().create([
                {'field_id': self.approve_state_id.id,
                 'value': 'approve',
                 'name': 'Waiting for Approval'},
                {'field_id': self.approve_state_id.id,
                 'value': 'approved',
                 'name': 'Approved'},
                {'field_id': self.approve_state_id.id,
                 'value': 'reject',
                 'name': 'Reject'}
            ])
        if not self.multi_state_field_id:
            self.multi_state_field_id = self.env[
                'ir.model.fields'].sudo().create({
                'ttype': 'boolean',
                'name': 'x_multi_state',
                'field_description': 'Multi State',
                'model_id': self.model_id.id,
            })
        if not self.approval_id:
            self.approval_id = self.env['ir.model.fields'].sudo().create({
                'ttype': 'many2one',
                'relation': 'dynamic.approval',
                'name': 'x_approval_id',
                'field_description': 'Approval Id',
                'readonly': False,
                'model_id': self.model_id.id,
                'tracking': True,
            })
        if not self.approval_model:
            approval_line_model = self.env['ir.model'].search(
                [('model', '=', 'approval.line')])
            self.approval_model = self.env['ir.model.fields'].sudo().create({
                'ttype': 'many2one',
                'relation': self.model_id.model,
                'name': 'x_approval_model' + str(self.id),
                'field_description': 'Approval Model',
                'model_id': approval_line_model.id,
            })
        if not self.check_old_records_id:
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                self.check_old_records_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_check_old_records',
                    'field_description': 'Disable Old Record  Approval',
                    'readonly': 'True',
                    'store': 'True',
                    'model_id': self.model_id.id,
                    'depends': 'stage_id,x_approval_id',
                    'compute': """
for record in self:
    for rec in record:
        if rec.x_check_old_records and rec.x_approval_id:
            rec.write({'x_multi_state': True})
        """
                })
            else:
                self.check_old_records_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_check_old_records',
                    'field_description': 'Disable Old Record  Approval',
                    'readonly': 'True',
                    'store': 'True',
                    'model_id': self.model_id.id,
                    'depends': 'state,x_approval_id',
                    'compute': """
for record in self:
    for rec in record:
        if rec.x_check_old_records and rec.x_approval_id:
            rec.write({'x_need_to_approve': True, 'x_multi_state': True})
        """
                })

        if not self.approver_ids or not self.env['ir.model.fields'].search(
                [('name', '=', 'x_approval_model' + str(self.id))]):
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                self.approver_ids = self.env['ir.model.fields'].sudo().create({
                    'ttype': 'one2many',
                    'relation': 'approval.line',
                    'relation_field': 'x_approval_model' + str(self.id),
                    'name': 'x_approver_ids',
                    'field_description': 'Approvers',
                    'model_id': self.model_id.id,
                    'readonly': 'True',
                    'store': 'True',
                    'depends': 'stage_id,x_approval_id,x_compute',
                    'compute': """
for rec in self:
    lines=[(5,0,0)]
    if not rec.x_approval_id.approval_method == 'hierarchy':
        if not rec.x_approval_id.state_specific_approval:
                for approver in rec.x_approval_id.users:
                    if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': approver.sequence,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.approver_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    elif rec.x_approval_id.enable_time_limit and rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': approver.sequence,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.individual_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    else:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': approver.sequence,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    if approver.model_stage_id:
                        val['approve_stage_id'] = approver.model_stage_id.id
                    if approver.approval_type_id.approval_type == 'custom':
                        if rec[approver.approver_field_id.name].ids:
                            val['approver_id'] = rec[approver.approver_field_id.name][0].id
                        if val['approver_id']:
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid and rec.id:
                                rec.message_post(body="Approval request failed since approval type is Custom and Custom field does not meet the requirements for Custom Approval.",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed because the custom field does not meet the requirements for Custom Approval'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                 '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                                
                            
                    elif approver.approval_type_id.approval_type == 'manager' and rec.create_uid:
                        if rec.create_uid.employee_id.parent_id.user_id:
                            val['approver_id'] = rec.create_uid.employee_id.parent_id.user_id.id
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid:
                                rec.message_post(body="Approval request failed since approval type is manager and no manager set for sale order created user",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Manager for you'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                    lines.append((0, 0, val))
                    rec.write({'x_approver_ids':lines})
        else:
            counter = 1
            for approver in rec.x_approval_id.users:
                  if approver.model_stage_id.rec_name == rec.stage_id.name:
                    if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': counter,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.approver_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    elif rec.x_approval_id.enable_time_limit and rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': counter,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.individual_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    else:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': counter,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    if rec.x_approval_id.approval_method == 'sequence':
                        counter += 1
                    if approver.model_stage_id:
                        val['approve_stage_id'] = approver.model_stage_id.id
                    if approver.approval_type_id.approval_type == 'custom':
                        if rec[approver.approver_field_id.name].ids:
                            val['approver_id'] = rec[approver.approver_field_id.name][0].id
                        if val['approver_id']:
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid and rec.id:
                                rec.message_post(body="Approval request failed since approval type is Custom and Custom field does not meet the requirements for Custom Approval.",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed because the custom field does not meet the requirements for Custom Approval'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                                
                            
                    elif approver.approval_type_id.approval_type == 'manager' and rec.create_uid:
                        if rec.create_uid.employee_id.parent_id.user_id:
                            val['approver_id'] = rec.create_uid.employee_id.parent_id.user_id.id
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid:
                                rec.message_post(body="Approval request failed since approval type is manager and no manager set for sale order created user",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Manager for you'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                 '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                    lines.append((0, 0, val))
                    rec.write({'x_approver_ids':lines}) 
    else:
        sequence = 0
        parent = self.env.user.employee_id.parent_id
        while parent.id:
            if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                 sequence += 1
                 val = {
                        'approver_id': parent.user_id.id,
                        'sequence': sequence,
                        'approval_status': 'approve',
                        'approval_id': rec.x_approval_id.id,
                        'time_limit' : rec.x_approval_id.timer,
                        'start_date': datetime.datetime.now().strftime(
                                                     '%Y-%m-%d %H:%M:%S')
                        }
            else:
                sequence += 1
                val = {
                    'approver_id': parent.user_id.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
            if not parent.user_id.id and rec.create_uid:
                rec.message_post(body="Approval request failed since there is no Related User set for "+ parent.name,
                              subject="Approval Request Failed")
                self.env['mail.mail'].sudo().create({
                                    'subject': rec._description +" Approval failed",
                                    'author_id': rec.create_uid.partner_id.id,
                                    'email_from': rec.x_approval_id.create_uid.name,
                                    'email_to': rec.create_uid.name,
                                    'body_html':
                                    '<table border=0 cellpadding=0 cellspacing=0 '
                                        'style="padding-top: 16px; background-color: '
                                        '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                        'color: #454748; width: 100%; '
                                        'border-collapse:separate;"><tr><td align=center>'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                        '<tbody>'
                                        '<!-- HEADER -->'
                                        '<tr>'
                                        '<td align=center style="min-width: 590px;">'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign=middle>'
                                        '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                        '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                         '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                         '</td>'
                                         '</tr>'
                                         '<tr>''<td colspan="2" style="text-align:center;">'
                                         '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                         '</td>''</tr>'
                                         '</table>'
                                         '</td>'
                                         '</tr>'
                                         '<!-- CONTENT -->'
                                         '<tr>'
                                         '<td align="center" style="min-width: 590px;">'
                                         '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                         '<tr>'
                                         '<td valign="top" style="font-size: 13px;">'
                                         '<div>'
                                         'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                         'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Related User set  for '+ parent.name + '.'
                                         '<br/>''<br/>'
                                         '<div style="margin: 16px 0px 16px 0px;">'
                                         '<span>'
                                        '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'                                         '</span>'
                                        '</div>'
                                        '<br/>''<br/>'
                                        'Best regards''<br/>'
                                        '</div>'
                                        '</td>'
                                        '</tr>'
                                        '<tr>'
                                        '<td style="text-align:center;">'
                                        '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                        '</td>'
                                        '</tr>'
                                        '</table>'
                                        '</td>'
                                        '</tr>'
                                        '<!-- FOOTER -->'
                                        '<tr>'
                                        '<td align="center" style="min-width: 590px;">'
                                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign="middle" align="left">'
                                        + self.env.company.name +
                                        '<br/>'
                                        + self.env.company.phone +
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                        '<t t-if="%s" % +self.env.company_id.email>'
                                        '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                        +self.env.company.email+
                                        '</a>'
                                        '</t>'
                                        '<br/>'
                                        '<t t-if="%s % +self.env.company.website+ ">'
                                        '</table>'
                                    }).send()
            lines.append((0, 0, val))
            rec.write({'x_approver_ids':lines})
            parent = parent.parent_id
        if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
             sequence += 1
             val = {
                    'approver_id': self.env.user.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'time_limit' : rec.x_approval_id.timer,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
        else:
            sequence += 1
            val = {
                'approver_id': self.env.user.id,
                'sequence': sequence,
                'approval_status': 'approve',
                'approval_id': rec.x_approval_id.id,
                'start_date': datetime.datetime.now().strftime(
                                             '%Y-%m-%d %H:%M:%S')
                }
        lines.append((0, 0, val))
        rec.write({'x_approver_ids':lines})
        for approver in self.env.user.employee_id.child_ids:
            sequence += 1
            if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                val = {
                    'approver_id': approver.user_id.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'time_limit' : rec.x_approval_id.timer,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
            else:
                val = {
                    'approver_id': approver.user_id.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
            if not approver.user_id.id and rec.create_uid:
                rec.message_post(body="Approval request failed since there is no Related User set for "+ approver.name,
                              subject="Approval Request Failed")
                self.env['mail.mail'].sudo().create({
                                    'subject': rec._description +" Approval failed",
                                    'author_id': rec.create_uid.partner_id.id,
                                    'email_from': rec.x_approval_id.create_uid.name,
                                    'email_to': rec.create_uid.name,
                                    'body_html':
                                    '<table border=0 cellpadding=0 cellspacing=0 '
                                        'style="padding-top: 16px; background-color: '
                                        '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                        'color: #454748; width: 100%; '
                                        'border-collapse:separate;"><tr><td align=center>'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                        '<tbody>'
                                        '<!-- HEADER -->'
                                        '<tr>'
                                        '<td align=center style="min-width: 590px;">'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign=middle>'
                                        '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                        '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                         '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                         '</td>'
                                         '</tr>'
                                         '<tr>''<td colspan="2" style="text-align:center;">'
                                         '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                         '</td>''</tr>'
                                         '</table>'
                                         '</td>'
                                         '</tr>'
                                         '<!-- CONTENT -->'
                                         '<tr>'
                                         '<td align="center" style="min-width: 590px;">'
                                         '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                         '<tr>'
                                         '<td valign="top" style="font-size: 13px;">'
                                         '<div>'
                                         'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                         'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Related User set  for '+ approver.name + '.'
                                         '<br/>''<br/>'
                                         '<div style="margin: 16px 0px 16px 0px;">'
                                         '<span>'
                                         '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                         '</span>'
                                        '</div>'
                                        '<br/>''<br/>'
                                        'Best regards''<br/>'
                                        '</div>'
                                        '</td>'
                                        '</tr>'
                                        '<tr>'
                                        '<td style="text-align:center;">'
                                        '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                        '</td>'
                                        '</tr>'
                                        '</table>'
                                        '</td>'
                                        '</tr>'
                                        '<!-- FOOTER -->'
                                        '<tr>'
                                        '<td align="center" style="min-width: 590px;">'
                                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign="middle" align="left">'
                                        + self.env.company.name +
                                        '<br/>'
                                        + self.env.company.phone +
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                        '<t t-if="%s" % +self.env.company_id.email>'
                                        '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                        +self.env.company.email+
                                        '</a>'
                                        '</t>'
                                        '<br/>'
                                        '<t t-if="%s % +self.env.company.website+ ">'
                                        '</table>'
                                    }).send()
            lines.append((0, 0, val))
            rec.write({'x_approver_ids':lines})
    """
                })
            else:
                self.approver_ids = self.env['ir.model.fields'].sudo().create({
                    'ttype': 'one2many',
                    'relation': 'approval.line',
                    'relation_field': 'x_approval_model' + str(self.id),
                    'name': 'x_approver_ids',
                    'field_description': 'Approvers',
                    'model_id': self.model_id.id,
                    'readonly': 'True',
                    'store': 'True',
                    'depends': 'state,x_approval_id,x_compute',
                    'compute': """
for rec in self:
    lines=[(5,0,0)]
    if not rec.x_approval_id.approval_method == 'hierarchy':
        if not rec.x_approval_id.state_specific_approval:
                for approver in rec.x_approval_id.users:
                    if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': approver.sequence,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.approver_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    elif rec.x_approval_id.enable_time_limit and rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': approver.sequence,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.individual_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    else:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': approver.sequence,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    if approver.model_states:
                        val['approve_state'] = approver.model_states.id
                    if approver.approval_type_id.approval_type == 'custom':
                        if rec[approver.approver_field_id.name].ids:
                            val['approver_id'] = rec[approver.approver_field_id.name][0].id
                        if val['approver_id']:
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid and rec.id:
                                rec.message_post(body="Approval request failed since approval type is Custom and Custom field does not meet the requirements for Custom Approval.",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed because the custom field does not meet the requirements for Custom Approval'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                 '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                    elif approver.approval_type_id.approval_type == 'manager' and rec.create_uid:
                        if rec.create_uid.employee_id.parent_id.user_id:
                            val['approver_id'] = rec.create_uid.employee_id.parent_id.user_id.id
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid:
                                rec.message_post(body="Approval request failed since approval type is manager and no manager set for sale order created user",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Manager for you'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                 '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                    lines.append((0, 0, val))
                    rec.write({'x_approver_ids':lines})
        else:
            counter = 1
            for approver in rec.x_approval_id.users:
                  if approver.model_states.value == rec.state:
                    if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': counter,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.approver_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    elif rec.x_approval_id.enable_time_limit and rec.x_approval_id.individual_time_limit:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': counter,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'time_limit' : approver.individual_time_limit,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    else:
                        val = {
                            'approver_id': approver.user_ids.id,
                            'sequence': counter,
                            'approval_type_id': approver.approval_type_id.id,
                            'approval_status': 'approve',
                            'approval_id': rec.x_approval_id.id,
                            'start_date': datetime.datetime.now().strftime(
                                                         '%Y-%m-%d %H:%M:%S')
                            }
                    if rec.x_approval_id.approval_method == 'sequence':
                        counter += 1
                    if approver.model_states:
                        val['approve_state'] = approver.model_states.id
                    if approver.approval_type_id.approval_type == 'custom':
                        if rec[approver.approver_field_id.name].ids:
                            val['approver_id'] = rec[approver.approver_field_id.name][0].id
                        if val['approver_id']:
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid and rec.id:
                                rec.message_post(body="Approval request failed since approval type is Custom and Custom field does not meet the requirements for Custom Approval.",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed because the custom field does not meet the requirements for Custom Approval'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                 '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                    elif approver.approval_type_id.approval_type == 'manager' and rec.create_uid:
                        if rec.create_uid.employee_id.parent_id.user_id:
                            val['approver_id'] = rec.create_uid.employee_id.parent_id.user_id.id
                            rec.x_approval_id.group_id.write({'user_ids': [(4,val['approver_id'],0)]})
                        else:
                            if rec.create_uid:
                                rec.message_post(body="Approval request failed since approval type is manager and no manager set for sale order created user",
                                          subject="Approval Request Failed")
                                self.env['mail.mail'].sudo().create({
                                            'subject': rec._description +" Approval failed",
                                            'author_id': rec.create_uid.partner_id.id,
                                            'email_from': rec.x_approval_id.create_uid.name,
                                            'email_to': rec.create_uid.name,
                                            'body_html':
                                            '<table border=0 cellpadding=0 cellspacing=0 '
                                                'style="padding-top: 16px; background-color: '
                                                '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                                'color: #454748; width: 100%; '
                                                'border-collapse:separate;"><tr><td align=center>'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                                '<tbody>'
                                                '<!-- HEADER -->'
                                                '<tr>'
                                                '<td align=center style="min-width: 590px;">'
                                                '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign=middle>'
                                                '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                                '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                 '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                 '</td>''</tr>'
                                                 '</table>'
                                                 '</td>'
                                                 '</tr>'
                                                 '<!-- CONTENT -->'
                                                 '<tr>'
                                                 '<td align="center" style="min-width: 590px;">'
                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                 '<tr>'
                                                 '<td valign="top" style="font-size: 13px;">'
                                                 '<div>'
                                                 'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                                 'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Manager for you'+ '.'
                                                 '<br/>''<br/>'
                                                 '<div style="margin: 16px 0px 16px 0px;">'
                                                 '<span>'
                                                 '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                                 '</span>'
                                                '</div>'
                                                '<br/>''<br/>'
                                                'Best regards''<br/>'
                                                '</div>'
                                                '</td>'
                                                '</tr>'
                                                '<tr>'
                                                '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                '</td>'
                                                '</tr>'
                                                '</table>'
                                                '</td>'
                                                '</tr>'
                                                '<!-- FOOTER -->'
                                                '<tr>'
                                                '<td align="center" style="min-width: 590px;">'
                                                '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                '<tr>'
                                                '<td valign="middle" align="left">'
                                                + self.env.company.name +
                                                '<br/>'
                                                + self.env.company.phone +
                                                '</td>'
                                                '<td valign="middle" align="right">'
                                                '<t t-if="%s" % +self.env.company_id.email>'
                                                '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                                +self.env.company.email+
                                                '</a>'
                                                '</t>'
                                                '<br/>'
                                                '<t t-if="%s % +self.env.company.website+ ">'
                                                '</table>'
                                            }).send()
                    lines.append((0, 0, val))
                    rec.write({'x_approver_ids':lines}) 
    else:
        sequence = 0
        parent = self.env.user.employee_id.parent_id
        while parent:
            if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                 sequence += 1
                 val = {
                        'approver_id': parent.user_id.id,
                        'sequence': sequence,
                        'approval_status': 'approve',
                        'approval_id': rec.x_approval_id.id,
                        'time_limit' : rec.x_approval_id.timer,
                        'start_date': datetime.datetime.now().strftime(
                                                     '%Y-%m-%d %H:%M:%S')
                        }
            else:
                sequence += 1
                val = {
                    'approver_id': parent.user_id.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
            if not parent.user_id.id and rec.create_uid:
                rec.message_post(body="Approval request failed since there is no Related User set for "+ parent.name,
                              subject="Approval Request Failed")
                self.env['mail.mail'].sudo().create({
                                    'subject': rec._description +" Approval failed",
                                    'author_id': rec.create_uid.partner_id.id,
                                    'email_from': rec.x_approval_id.create_uid.name,
                                    'email_to': rec.create_uid.name,
                                    'body_html':
                                    '<table border=0 cellpadding=0 cellspacing=0 '
                                        'style="padding-top: 16px; background-color: '
                                        '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                        'color: #454748; width: 100%; '
                                        'border-collapse:separate;"><tr><td align=center>'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                        '<tbody>'
                                        '<!-- HEADER -->'
                                        '<tr>'
                                        '<td align=center style="min-width: 590px;">'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign=middle>'
                                        '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                        '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                         '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                         '</td>'
                                         '</tr>'
                                         '<tr>''<td colspan="2" style="text-align:center;">'
                                         '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                         '</td>''</tr>'
                                         '</table>'
                                         '</td>'
                                         '</tr>'
                                         '<!-- CONTENT -->'
                                         '<tr>'
                                         '<td align="center" style="min-width: 590px;">'
                                         '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                         '<tr>'
                                         '<td valign="top" style="font-size: 13px;">'
                                         '<div>'
                                         'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                         'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Related User set  for '+ parent.name + '.'
                                         '<br/>''<br/>'
                                         '<div style="margin: 16px 0px 16px 0px;">'
                                         '<span>'
                                         '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                         '</span>'
                                        '</div>'
                                        '<br/>''<br/>'
                                        'Best regards''<br/>'
                                        '</div>'
                                        '</td>'
                                        '</tr>'
                                        '<tr>'
                                        '<td style="text-align:center;">'
                                        '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                        '</td>'
                                        '</tr>'
                                        '</table>'
                                        '</td>'
                                        '</tr>'
                                        '<!-- FOOTER -->'
                                        '<tr>'
                                        '<td align="center" style="min-width: 590px;">'
                                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign="middle" align="left">'
                                        + self.env.company.name +
                                        '<br/>'
                                        + self.env.company.phone +
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                        '<t t-if="%s" % +self.env.company_id.email>'
                                        '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                        +self.env.company.email+
                                        '</a>'
                                        '</t>'
                                        '<br/>'
                                        '<t t-if="%s % +self.env.company.website+ ">'
                                        '</table>'
                                    }).send()
            lines.append((0, 0, val))
            rec.write({'x_approver_ids':lines})
            if parent.parent_id != self.env.user.employee_id.parent_id:
                parent = parent.parent_id
            else:
                parent = False
        if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
             sequence += 1
             val = {
                    'approver_id': self.env.user.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'time_limit' : rec.x_approval_id.timer,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
        else:
            sequence += 1
            val = {
                'approver_id': self.env.user.id,
                'sequence': sequence,
                'approval_status': 'approve',
                'approval_id': rec.x_approval_id.id,
                'start_date': datetime.datetime.now().strftime(
                                             '%Y-%m-%d %H:%M:%S')
                }
        lines.append((0, 0, val))
        rec.write({'x_approver_ids':lines})            
        for approver in self.env.user.employee_id.child_ids:
            sequence += 1
            if rec.x_approval_id.enable_time_limit and not rec.x_approval_id.individual_time_limit:
                val = {
                    'approver_id': approver.user_id.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'time_limit' : rec.x_approval_id.timer,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
            else:
                val = {
                    'approver_id': approver.user_id.id,
                    'sequence': sequence,
                    'approval_status': 'approve',
                    'approval_id': rec.x_approval_id.id,
                    'start_date': datetime.datetime.now().strftime(
                                                 '%Y-%m-%d %H:%M:%S')
                    }
            if not approver.user_id.id and rec.create_uid:
                rec.message_post(body="Approval request failed since there is no Related User set for "+ approver.name,
                              subject="Approval Request Failed")
                self.env['mail.mail'].sudo().create({
                                    'subject': rec._description +" Approval failed",
                                    'author_id': rec.create_uid.partner_id.id,
                                    'email_from': rec.x_approval_id.create_uid.name,
                                    'email_to': rec.create_uid.name,
                                    'body_html':
                                    '<table border=0 cellpadding=0 cellspacing=0 '
                                        'style="padding-top: 16px; background-color: '
                                        '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                                        'color: #454748; width: 100%; '
                                        'border-collapse:separate;"><tr><td align=center>'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                        '<tbody>'
                                        '<!-- HEADER -->'
                                        '<tr>'
                                        '<td align=center style="min-width: 590px;">'
                                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign=middle>'
                                        '<span style="font-size: 10px;">Approval Failed</span><br/>'
                                        '<span style="font-size: 20px; font-weight: bold;">'+ rec.name + '</span>'
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                         '<img src="/logo.png?company=" + self.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                         '</td>'
                                         '</tr>'
                                         '<tr>''<td colspan="2" style="text-align:center;">'
                                         '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                         '</td>''</tr>'
                                         '</table>'
                                         '</td>'
                                         '</tr>'
                                         '<!-- CONTENT -->'
                                         '<tr>'
                                         '<td align="center" style="min-width: 590px;">'
                                         '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                         '<tr>'
                                         '<td valign="top" style="font-size: 13px;">'
                                         '<div>'
                                         'Dear' + ' ' + rec.create_uid.name + ',' '<br/>''<br/>'
                                         'Your Approval Request for ' + rec.name + ' ' + 'has been failed, since there is no Related User set  for '+ approver.name + '.'
                                         '<br/>''<br/>'
                                         '<div style="margin: 16px 0px 16px 0px;">'
                                         '<span>'
                                         '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="' + str(self.env["ir.config_parameter"].sudo().get_param("web.base.url")) + '/odoo/' + str(rec._name) + '/' + str(rec.id) + '">View Record</a>'
                                         '</span>'
                                        '</div>'
                                        '<br/>''<br/>'
                                        'Best regards''<br/>'
                                        '</div>'
                                        '</td>'
                                        '</tr>'
                                        '<tr>'
                                        '<td style="text-align:center;">'
                                        '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                        '</td>'
                                        '</tr>'
                                        '</table>'
                                        '</td>'
                                        '</tr>'
                                        '<!-- FOOTER -->'
                                        '<tr>'
                                        '<td align="center" style="min-width: 590px;">'
                                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign="middle" align="left">'
                                        + self.env.company.name +
                                        '<br/>'
                                        + self.env.company.phone +
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                        '<t t-if="%s" % +self.env.company_id.email>'
                                        '<a href="mailto:%s % +self.env.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                                        +self.env.company.email+
                                        '</a>'
                                        '</t>'
                                        '<br/>'
                                        '<t t-if="%s % +self.env.company.website+ ">'
                                        '</table>'
                                    }).send()
            lines.append((0, 0, val))
            rec.write({'x_approver_ids':lines})
    """
                })

        if not self.multi_approver_status_checker_id:
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                self.multi_approver_status_checker_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_approver_status_checker',
                    'field_description': 'Multi Approver Status checker',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status, stage_id',
                    'compute': """
for record in self:
  record.write({'x_approver_status_checker': False})
  if not record.x_approval_id:
    record.write({'x_approver_status_checker': False})
    break
  if record.stage_id.name not in record.x_approval_id.record_ids.mapped('rec_name'):
    record.write({'x_approver_status_checker': False})
    record.write({'x_need_to_approve': False})
  elif record.x_approver_ids and self.env.uid in record.x_approver_ids.mapped('approver_id').ids:
    for rec in record.x_approver_ids:
      if rec.sequence-1 == 0:
        if rec.approval_status != 'approved':
          if rec.approver_id.id == self.env.uid:
            record.write({'x_approver_status_checker': True})
            record.write({'x_need_to_approve': True})
            break
      else:
        for i in record.x_approver_ids.filtered(lambda l: l.approval_status != 'approved').sorted(
            lambda l: l.sequence):
            if i.approver_id.id == self.env.uid:
              record.write({'x_approver_status_checker': True})
              record.write({'x_need_to_approve': True})
            break
"""
                })
            else:
                self.multi_approver_status_checker_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_approver_status_checker',
                    'field_description': 'Multi Approver Status checker',
                    'model_id': self.model_id.id,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status, state',
                    'compute': """
for record in self:
  record.write({'x_approver_status_checker': False})
  if not record.x_approval_id:
    record.write({'x_approver_status_checker': False})
    break
  if record.state not in record.x_approval_id.model_states.mapped('value'):
    record.write({'x_approver_status_checker': False})
  elif record.x_approver_ids and self.env.uid in record.x_approver_ids.mapped('approver_id').ids:
    for rec in record.x_approver_ids:
      if rec.sequence-1 == 0:
        if rec.approval_status != 'approved':
          if rec.approver_id.id == self.env.uid:
            record.write({'x_approver_status_checker': True})
            break
      else:
        for i in record.x_approver_ids.filtered(lambda l: l.approval_status != 'approved').sorted(
            lambda l: l.sequence):
            if i.approver_id.id == self.env.uid:
              record.write({'x_approver_status_checker': True})
            break
"""
                })
        if not self.header_status_checker:
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                self.header_status_checker = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_header_status_checker',
                    'field_description': 'X Header Status Checker',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status, stage_id',
                    'compute': """
for record in self:
    if not record.x_approval_id.state_specific_approval:
        if not record.x_approval_id:
            record.write({'x_header_status_checker': False})
            break
        if str(record.stage_id.id) not in record.x_approval_id.record_ids.mapped('rec_id'):
            record.write({'x_header_status_checker': False})
        elif record.x_approve_state == 'approved':
            record.write({'x_header_status_checker': False})
        else:
            record.write({'x_header_status_checker': True})
            record.write({'x_need_to_approve': True})
    else:
        if not record.x_approval_id:
            record.write({'x_header_status_checker': False})
            break
        if record.stage_id.name not in record.x_approver_ids.approve_stage_id.mapped('rec_name'):
            record.write({'x_header_status_checker': False})
        elif record.x_approve_state == 'approved':
            record.write({'x_header_status_checker': False})
        else:
            record.write({'x_header_status_checker': True})
"""
                })
            else:
                self.header_status_checker = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_header_status_checker',
                    'field_description': 'X Header Status Checker',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status, state',
                    'compute': """
for record in self:
  if not record.x_approval_id.state_specific_approval:
      if not record.x_approval_id:
        record.write({'x_header_status_checker': False})
        break
      if record.state not in record.x_approval_id.model_states.mapped('value'):
        record.write({'x_header_status_checker': False})
      elif record.x_approve_state == 'approved':
        record.write({'x_header_status_checker': False})
      else:
        record.write({'x_header_status_checker': True})
  else:
      if not record.x_approval_id:
        record.write({'x_header_status_checker': False})
        break
      if record.state not in record.x_approval_id.users.model_states.mapped('value'):
        record.write({'x_header_status_checker': False})
      elif record.x_approve_state == 'approved':
        record.write({'x_header_status_checker': False})
      else:
          record.write({'x_header_status_checker': True})
"""
                })

        if not self.group_id:
            self.group_id = group_obj.sudo().create(
                {'name': 'Approver' + ' ' + self.model_id.name,
                 'privilege_id': self.category_id.id,
                 'is_approve': True
                 })
            self.group_id.user_ids = self.users.user_ids
            group_xml_id = _export_xml_id(self.group_id)

        else:
            self.group_id.user_ids = self.users.user_ids

        if self.remove_reports:
            data = self.env[self.model_id.model].get_views([(None, 'form')],
                                                           {'toolbar': True,
                                                            'submenu': False})
            if 'print' in data['views']['form']['toolbar']:
                report_ids = [x.get('id') for x in
                              data['views']['form']['toolbar']['print']]
                reports = self.env['ir.actions.report'].browse(report_ids)
                self.report_action_ids = reports
                reports.unlink_action()
        if not self.approve_server_action_id:
            code = ("""
users =  record.x_approver_ids.filtered(lambda l: l.approver_id == env.user)
for user in users:
    user.write({'approval_status' : 'approved','approval_email_status': 'sent','end_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    parallel_approvers_case = record.x_approver_ids.mapped('sequence')
    record.write({'x_check_parllel_approval': False})
    if len(parallel_approvers_case) > 1:
        if parallel_approvers_case[1] == parallel_approvers_case[0]:
            record.write({'x_check_parllel_approval': True})
        if not record.x_check_parllel_approval:
            if user.sequence == 1:
                if user.end_date and user.start_date:
                    duration =  (user.end_date - user.start_date)
                    user.write({'approval_duration' : duration})
            else:
                    current_user_sequence = user.sequence
                    prv_approver = record.x_approver_ids.filtered(lambda l: l.sequence == current_user_sequence - 1)
                    if user.end_date and prv_approver.end_date:
                        ind_duartion = (user.end_date - prv_approver.end_date)
                        user.write({'approval_duration' : ind_duartion})
        else:
             if user.sequence == 1 :
                 if user.end_date and user.start_date:
                    duration =  (user.end_date - user.start_date)
                    user.write({'approval_duration' : duration})
    else:
        if user.sequence == 1 :
            if user.end_date and user.start_date:
                duration =  (user.end_date - user.start_date)
                user.write({'approval_duration' : duration})
    user_id = env.user
    base_url = record.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip('/')

    mail_url = base_url + '/odoo/' + str(record._name) + '/' + str(record.id)
    record.env['mail.mail'].sudo().create({
                    'subject': record._description + ' Approved',
                    'author_id': str(user_id.partner_id.id),
                    'email_from': str(user.approver_id.login),
                    'email_to': str(record.create_uid.login),
                    'body_html':
                        '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">'
                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                        '<tbody>'
                        '<!-- HEADER -->'
                        '<tr>'
                        '<td align="center" style="min-width: 590px;">'
                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                        '<tr>'
                        '<td valign="middle">'
                        '<span style="font-size: 10px;">' 'Approval Request Approved''</span>''<br/>' +
                        '<span style="font-size: 20px; font-weight: bold;">' + record.name + '</span>'
                         '</td>'
                         '<td valign="middle" align="right">'
                         '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                         '</td>'
                         '</tr>'
                         '<tr>''<td colspan="2" style="text-align:center;">'
                         '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                         '</td>''</tr>'
                         '</table>'
                         '</td>'
                         '</tr>'
                         '<!-- CONTENT -->'
                         '<tr>'
                         '<td align="center" style="min-width: 590px;">'
                         '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                         '<tr>'
                         '<td valign="top" style="font-size: 13px;">'
                         '<div>'
                         'Dear' + ' ' + record.create_uid.name + ',' '<br/>''<br/>'
                         'Your  approval  request ' + record.name + ' ' + 'is Approved by ' +user.approver_id.name+ '.'
                         '<br/>''<br/>'
                         '<div style="margin: 16px 0px 16px 0px;">'
                         '<span>'
                         '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href=' + mail_url + '>View Record</a>'
                         '</span>'
                        '</div>'
                        '<br/>''<br/>'
                        'Best regards''<br/>'
                        '</div>'
                        '</td>'
                        '</tr>'
                        '<tr>'
                        '<td style="text-align:center;">'
                        '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                        '</td>'
                        '</tr>'
                        '</table>'
                        '</td>'
                        '</tr>'
                        '<!-- FOOTER -->'
                        '<tr>'
                        '<td align="center" style="min-width: 590px;">'
                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                        '<tr>'
                        '<td valign="middle" align="left">'
                        + user_id.company_id.name +
                        '<br/>'
                        + user_id.company_id.phone +
                        '</td>'
                        '<td valign="middle" align="right">'
                        '<t t-if="%s" % +user_id.company_id.email>'
                        '<a href="mailto:%s % +user_id.company_id.email+" style="text-decoration:none; color: #5e6061;">'
                        +user_id.company_id.email+
                        '</a>'
                        '</t>'
                        '<br/>'
                        '<t t-if="%s % +user_id.company_id.website+ ">'
                        '<a href="%s % +user_id.company_id.website+" style="text-decoration:none; color: #5e6061;">'
                        +user_id.company_id.website+
                        '</a>'
                        '</t>'
                        '</td>'
                        '</tr>'
                        '</table>'
                        '</td>'
                        '</tr>'
                        '</tbody>'
                        '</table>'
                }).send()
    current_user = record.x_approver_ids.filtered(lambda l: l.approver_id == env.user)
    sequ = current_user[0].sequence + 1
    next_user_id = record.x_approver_ids.filtered(lambda l: l.sequence == sequ)
    if next_user_id and next_user_id.approver_id:
        record.env['mail.mail'].sudo().create({
                        'subject': record._description + ' Approval',
                        'author_id': str(user_id.partner_id.id),
                        'email_from': str(record.create_uid.login),
                        'email_to': str(next_user_id.approver_id.login),
                        'body_html':
                            '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                            '<tbody>'
                            '<!-- HEADER -->'
                            '<tr>'
                            '<td align="center" style="min-width: 590px;">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                            '<tr>'
                            '<td valign="middle">'
                            '<span style="font-size: 10px;">' 'Need Approval''</span>''<br/>' +
                            '<span style="font-size: 20px; font-weight: bold;">' + record.name + '</span>'
                             '</td>'
                             '<td valign="middle" align="right">'
                             '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                             '</td>'
                             '</tr>'
                             '<tr>''<td colspan="2" style="text-align:center;">'
                             '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                             '</td>''</tr>'
                             '</table>'
                             '</td>'
                             '</tr>'
                             '<!-- CONTENT -->'
                             '<tr>'
                             '<td align="center" style="min-width: 590px;">'
                             '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                             '<tr>'
                             '<td valign="top" style="font-size: 13px;">'
                             '<div>'
                             'Dear' + ' ' + str(next_user_id.approver_id.name) + ',' '<br/>''<br/>'
                             'You have a new approval request from ' + record.create_uid.name + ' ' + 'of ' +record.name+ '.' '<br/>'
                             '<span style="color: red;">' 'The approval time limit of the request is ' + str(user.time_limit) + ' Hour .' '</span>'
                             '<br/>''<br/>'
                             '<div style="margin: 16px 0px 16px 0px;">'
                             '<span>'
                             '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href=' + mail_url + '>View Record</a>'
                             '</span>'
                            '</div>'
                            '<br/>''<br/>'
                            'Best regards''<br/>'
                            '</div>'
                            '</td>'
                            '</tr>'
                            '<tr>'
                            '<td style="text-align:center;">'
                            '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                            '</td>'
                            '</tr>'
                            '</table>'
                            '</td>'
                            '</tr>'
                            '<!-- FOOTER -->'
                            '<tr>'
                            '<td align="center" style="min-width: 590px;">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                            '<tr>'
                            '<td valign="middle" align="left">'
                            + str(next_user_id.approver_id.company_id.name) +
                            '<br/>'
                            + str(next_user_id.approver_id.company_id.phone) +
                            '</td>'
                            '<td valign="middle" align="right">'
                            '<t t-if="%s" % + str(next_user_id.approver_id.company_id.email) +>'
                            '<a href="mailto:%s % + str(next_user_id.approver_id.company_id.email) +" style="text-decoration:none; color: #5e6061;">'
                            + str(next_user_id.approver_id.company_id.email) +
                            '</a>'
                            '</t>'
                            '<br/>'
                            '<t t-if="%s % + str(next_user_id.approver_id.company_id.website) + ">'
                            '<a href="%s % + str(next_user_id.approver_id.company_id.website) +" style="text-decoration:none; color: #5e6061;">'
                            + str(next_user_id.approver_id.company_id.website) +
                            '</a>'
                            '</t>'
                            '</td>'
                            '</tr>'
                            '</table>'
                            '</td>'
                            '</tr>'
                            '</tbody>'
                            '</table>'
                    }).send()
    if current_user[0].sequence == next_user_id.sequence - 1:
        next_user_id.write({'approval_email_status': 'sent', 'start_date': datetime.datetime.now().strftime(
                                         '%Y-%m-%d %H:%M:%S') })
    else:
        next_user_id.write({'approval_email_status': 'sent'})
    current_moodel = record._context.get("active_model")
    if 'approve' not in record.x_approver_ids.mapped('approval_status'):
        record.write({'x_approve':True, 'x_approve_state':'approved', 'x_need_to_approve': False,'x_multi_state': True})
    if record.env['ir.model'].search([('model', '=', current_moodel)]).is_mail_thread:
        record.message_post(body=record._description+" is Approved, and the Approval Duration is " + str(user.approval_duration)+" .", subject="Approved")
        record.message_post(body="The approval request is Approved and Info mail sent to the created user " + record.create_uid.name+" .", subject="Approved Mail")
        parallel_approvers_case = record.x_approver_ids.mapped('sequence')
        if next_user_id and next_user_id.approver_id:
            if len(parallel_approvers_case) > 1 and parallel_approvers_case[1] != parallel_approvers_case[0]:
                record.message_post(body="The " + record._description + " Approval request email is sent to the next approver " + next_user_id.approver_id.name+" .", subject="Email Sent")
""")
            self.approve_server_action_id = self.env[
                'ir.actions.server'].sudo().create({'name': approve_action_name,
                                                    'model_id': self.model_id.id,
                                                    'state': 'code',
                                                    'code': code})

        code = ("""
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'reject.reason',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Approval Reject Reason',
            'context': {'origin':record},
        }""")

        if not self.reject_server_action_id:
            self.reject_server_action_id = self.env[
                'ir.actions.server'].sudo().create({'name': reject_action_name,
                                                    'model_id': self.model_id.id,
                                                    'state': 'code',
                                                    'code': code})
        if not self.re_send_server_action_id:
            code = ("""
current_moodel = record._context.get("active_model")
for user in record.x_approver_ids.filtered(lambda l: l.approval_status != 'approve'):
    user.write({'approval_status' : 'approve', 'approval_email_status': 'draft'})
    if 'approve' in record.x_approver_ids.mapped('approval_status'):
        record.write({'x_approve':True, 'x_approve_state':'approve'})
    if record.env['ir.model'].search([('model', '=', current_moodel)]).is_mail_thread:
        record.message_post(body=record._description+" Approval request is resubmitted .", subject="Resubmitted")
    """)
            self.re_send_server_action_id = self.env[
                'ir.actions.server'].sudo().create(
                {'name': re_send_action_name,
                 'model_id': self.model_id.id,
                 'state': 'code',
                 'code': code})

        if not self.email_status_checker_id:
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                self.email_status_checker_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_email_status_checker',
                    'field_description': 'Approval Email Status checker',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status,stage_id',
                    'compute': """
user_id = self.env.user
subject = self._description + ' Approval'
current_moodel = self._context.get("active_model")
for record in self:
    record.write({'x_email_status_checker': False})
    if record.x_approver_ids and record.id:
        for rec in record.x_approver_ids:
          if rec.sequence == 1 and rec.approver_id.name:
            if rec.approval_email_status != 'sent' and rec.approval_status != 'approved':
                rec.write({'approval_email_status': 'sent'})
                record.write({'x_email_status_checker': True})
                if record.x_email_status_checker and rec.approver_id:
                    mail_url = (
                        str(self.env["ir.config_parameter"].sudo().get_param("web.base.url"))
                        + '/odoo/'
                        + str(record._name)
                        + '/'
                        + str(record.id)
                    )
                     self.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'author_id': str(user_id.partner_id.id),
                        'email_from': str(record.create_uid.login),
                        'email_to': str(rec.approver_id.login),
                        'body_html':
                        '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">'
                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                        '<tbody>'
                            '<!-- HEADER -->'
                            '<tr>'
                                '<td align="center" style="min-width: 590px;">'
                                    '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                            '<td valign="middle">'
                                                '<span style="font-size: 10px;">' 'Need Approval''</span>''<br/>' +
                                                '<span style="font-size: 20px; font-weight: bold;">' + record.name + '</span>'
                                            '</td>'
                                            '<td valign="middle" align="right">'
                                                '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                            '</td>'
                                        '</tr>'
                                        '<tr>''<td colspan="2" style="text-align:center;">'
                                            '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                        '</td>''</tr>'
                                    '</table>'
                                '</td>'
                            '</tr>'
                            '<!-- CONTENT -->'
                             '<tr>'
                                '<td align="center" style="min-width: 590px;">'
                                    '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                            '<td valign="top" style="font-size: 13px;">'
                                            '<div>'
                                                'Dear' + ' ' +rec.approver_id.name+ ',' '<br/>''<br/>'
                                                'You have a new Approval  request from' + ' ' +record.create_uid.name + ' ' + 'of' + ' ' + record.name + '.' '<br/>'
                                                '<span style="color: red;">' 'The approval time limit of the request is ' + str(rec.time_limit) + ' Hour .' '</span>'
                                                '<br/>''<br/>'
                                                '<div style="margin: 16px 0px 16px 0px;">'
                                                    '<span>'
                                                        '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href='+mail_url+'>View Record</a>'
                                                    '</span>'
                                                '</div>'
                                                '<br/>''<br/>' +
                                                'Best regards' + '<br/>'
                                            '</div>'
                                            '</td>'
                                        '</tr>'
                                        '<tr>'
                                            '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                            '</td>'
                                        '</tr>'
                                    '</table>'
                                '</td>'
                            '</tr>'
                            '<!-- FOOTER -->'
                            '<tr>'
                            '<td align="center" style="min-width: 590px;">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                            '<tr>'
                            '<td valign="middle" align="left">'
                            +user_id.company_id.name+
                            '<br/>'
                            +user_id.company_id.phone+
                            '</td>'
                            '<td valign="middle" align="right">'
                            '<t t-if="%s" % +user_id.company_id.email>'
                            '<a href="mailto:%s % +user_id.company_id.email+" style="text-decoration:none; color: #535556;">'
                            +user_id.company_id.email+
                            '</a>'
                            '</t>'
                            '<br/>'
                            '<t t-if="%s % +user_id.company_id.website+ ">'
                            '<a href="%s % +user_id.company_id.website+" style="text-decoration:none; color: #535556;">'
                            +user_id.company_id.website+
                            '</a>'
                            '</t>'
                            '</td>'
                            '</tr>'
                            '</table>'
                            '</td>'
                            '</tr>'
                        '</tbody>'
                        '</table>'
                     }).send()
                if record.env['ir.model'].search([('model', '=', self._name)]).is_mail_thread:
                    if record.company_id.id in record.x_approver_ids.approval_id.company_id.ids:
                        record.message_post(body=record._description+" approval request mail is sent to the first approver " +rec.approver_id.name+ " .", subject="First Approval Mail Shared")
          if rec.approval_type_id.approval_type == 'manager' and self.create_uid:
              if self.create_uid.employee_id.parent_id.user_id:
                rec.write({'approver_id': self.create_uid.employee_id.parent_id.user_id})"""
                })
            else:
                self.email_status_checker_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_email_status_checker',
                    'field_description': 'Approval Email Status checker',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status,state',
                    'compute': """
user_id = self.env.user
subject = self._description + ' Approval'
current_moodel = self._context.get("active_model")
for record in self: 
    record.write({'x_email_status_checker': False})
    if record.x_approver_ids and record.id:
        for rec in record.x_approver_ids:
          if rec.sequence == 1 and rec.approver_id.name:
            if rec.approval_email_status != 'sent' and rec.approval_status != 'approved':
                record.write({'x_approve_state': 'approve'})
                rec.write({'approval_email_status': 'sent'})
                record.write({'x_email_status_checker': True})
                if record.x_email_status_checker and rec.approver_id:
                     mail_url = (
                        str(self.env["ir.config_parameter"].sudo().get_param("web.base.url"))
                        + '/odoo/'
                        + str(record._name)
                        + '/'
                        + str(record.id)
                    )
                     self.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'author_id': str(user_id.partner_id.id),
                        'email_from': str(record.create_uid.login),
                        'email_to': str(rec.approver_id.login),
                        'body_html':
                        '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">'
                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                        '<tbody>'
                            '<!-- HEADER -->'
                            '<tr>'
                                '<td align="center" style="min-width: 590px;">'
                                    '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                            '<td valign="middle">'
                                                '<span style="font-size: 10px;">' 'Need Approval''</span>''<br/>' +
                                                '<span style="font-size: 20px; font-weight: bold;">' + record.name + '</span>'
                                            '</td>'
                                            '<td valign="middle" align="right">'
                                                '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                            '</td>'
                                        '</tr>'
                                        '<tr>''<td colspan="2" style="text-align:center;">'
                                            '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                        '</td>''</tr>'
                                    '</table>'
                                '</td>'
                            '</tr>'
                            '<!-- CONTENT -->'
                             '<tr>'
                                '<td align="center" style="min-width: 590px;">'
                                    '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                            '<td valign="top" style="font-size: 13px;">'
                                            '<div>'
                                                'Dear' + ' ' +rec.approver_id.name+ ',' '<br/>''<br/>'
                                                'You have a new Approval  request from' + ' ' +record.create_uid.name + ' ' + 'of' + ' ' + record.name + '.' '<br/>'
                                                '<span style="color: red;">' 'The approval time limit of the request is ' + str(rec.time_limit) + ' Hour .' '</span>'
                                                '<br/>''<br/>'
                                                '<div style="margin: 16px 0px 16px 0px;">'
                                                    '<span>'
                                                        '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href='+mail_url+'>View Record</a>'
                                                    '</span>'
                                                '</div>'
                                                '<br/>''<br/>' +
                                                'Best regards' + '<br/>'
                                            '</div>'
                                            '</td>'
                                        '</tr>'
                                        '<tr>'
                                            '<td style="text-align:center;">'
                                                '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                            '</td>'
                                        '</tr>'
                                    '</table>'
                                '</td>'
                            '</tr>'
                            '<!-- FOOTER -->'
                            '<tr>'
                            '<td align="center" style="min-width: 590px;">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                            '<tr>'
                            '<td valign="middle" align="left">'
                            +user_id.company_id.name+
                            '<br/>'
                            +user_id.company_id.phone+
                            '</td>'
                            '<td valign="middle" align="right">'
                            '<t t-if="%s" % +user_id.company_id.email>'
                            '<a href="mailto:%s % +user_id.company_id.email+" style="text-decoration:none; color: #535556;">'
                            +user_id.company_id.email+
                            '</a>'
                            '</t>'
                            '<br/>'
                            '<t t-if="%s % +user_id.company_id.website+ ">'
                            '<a href="%s % +user_id.company_id.website+" style="text-decoration:none; color: #535556;">'
                            +user_id.company_id.website+
                            '</a>'
                            '</t>'
                            '</td>'
                            '</tr>'
                            '</table>'
                            '</td>'
                            '</tr>'
                        '</tbody>'
                        '</table>'
                     }).send()
                if record.env['ir.model'].search([('model', '=', self._name)]).is_mail_thread:
                    if record.company_id.id in record.x_approver_ids.approval_id.company_id.ids:
                        record.message_post(body=record._description+" approval request mail is sent to the first approver " +rec.approver_id.name+ " .", subject="First Approval Mail Shared")
          if rec.approval_type_id.approval_type == 'manager' and self.create_uid:
              if self.create_uid.employee_id.parent_id.user_id:
                  rec.write({'approver_id': self.create_uid.employee_id.parent_id.user_id})"""
                })

        if not self.fully_approved_field_id:
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                self.fully_approved_field_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_fully_approved',
                    'field_description': 'Fully Approved',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status, stage_id',
                    'compute': """
for record in self:
 current_moodel = record.x_approval_id.model_id.model
 if not record.x_approver_ids.filtered(lambda l: l.approval_status != 'approved'):
  record.write({'x_fully_approved' : True})
  reports_data = self.env['ir.actions.report'].search([('model', '=', current_moodel)])
  reports_data.create_action()
 if record.x_multi_state:
  reports_data = self.env['ir.actions.report'].search([('model', '=', current_moodel)])
  reports_data.unlink_action()
                 """
                })
            else:
                self.fully_approved_field_id = self.env[
                    'ir.model.fields'].sudo().create({
                    'ttype': 'boolean',
                    'name': 'x_fully_approved',
                    'field_description': 'Fully Approved',
                    'model_id': self.model_id.id,
                    'readonly': False,
                    'store': False,
                    'depends': 'x_approver_ids.approval_status, state',
                    'compute': """
for record in self:
 current_moodel = record.x_approval_id.model_id.model
 if not record.x_approver_ids.filtered(lambda l: l.approval_status != 'approved'):
  record.write({'x_fully_approved' : True})
  reports_data = self.env['ir.actions.report'].search([('model', '=', current_moodel)])
  reports_data.create_action()
 if record.x_multi_state:
  reports_data = self.env['ir.actions.report'].search([('model', '=', current_moodel)])
  reports_data.unlink_action()
                 """
                })

        if not self.check_approval_delay:
            if self.enable_time_limit:
                sheduled_action_name = self.model_id.name + "Approval Delay checker"
                model = self.model_id.model
                model_name = self.model_id.name
                self.check_approval_delay = self.env['ir.cron'].sudo(). \
                    create({'name': sheduled_action_name,
                            'active': True,
                            'model_id': self.model_id.id,
                            'interval_number': self.delay_time,
                            'interval_type': self.delay_type,
                            'nextcall': datetime.now(),
                            # 'numbercall': -1,
                            'priority': 5,
                            # 'doall': True,
                            'code': """
for x_approval_id in env['dynamic.approval'].sudo().search([('model_id', '=', '%s'""" % model_name + """)]):
  if x_approval_id.is_reminder:
    data = env['%s'""" % model + """].search([('x_approve_state', '=', 'approve'),('x_check_old_records', '=', False),('x_reminder_mail', '=', False)])
  else:
    data = env['%s'""" % model + """].search([('x_approve_state', '=', 'approve'),('x_check_old_records', '=', False)])
for record in data:
     for delayed_approver in record.x_approver_ids:
            hour = delayed_approver.start_date.hour
            dealy_date = delayed_approver.start_date.replace(
                hour=delayed_approver.time_limit + hour)
            if dealy_date <= datetime.datetime.now() and delayed_approver.approval_status == 'approve':
                delayed_approver.write({'delay': True, 'authority_email_status': 'sent'})
                break
     base_url = env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip('/')
     mail_url = base_url + '/odoo/' + str(record._name) + '/' + str(record.id)
     if record.x_approval_id.enable_time_limit:
        for approver in record.x_approver_ids.filtered(lambda l: l.time_limit and l.approval_status == 'approve' and l.delay):
            if not approver.is_send:
                env['mail.mail'].sudo().create({
                    'subject': record._description + ' Approval Delayed',
                    'author_id': str(approver.approver_id.partner_id.id),
                    'email_from': str(approver.approver_id.login),
                    'email_to': str(record.create_uid.login),
                    'body_html': '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                            '<tbody>'
                            '<!-- HEADER -->'
                            '<tr>'
                            '<td align="center" style="min-width: 590px;">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                            '<tr>'
                            '<td valign="middle">'
                            '<span style="font-size: 10px;">' 'Approval Delayed''</span>''<br/>' +
                            '<span style="font-size: 20px; font-weight: bold;">' + record.name + '</span>'
                             '</td>'
                             '<td valign="middle" align="right">'
                             '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                             '</td>'
                             '</tr>'
                             '<tr>''<td colspan="2" style="text-align:center;">'
                             '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                             '</td>''</tr>'
                             '</table>'
                             '</td>'
                             '</tr>'
                             '<!-- CONTENT -->'
                             '<tr>'
                             '<td align="center" style="min-width: 590px;">'
                             '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                             '<tr>'
                             '<td valign="top" style="font-size: 13px;">'
                             '<div>'
                             'Dear' + ' ' + record.create_uid.name + ',' '<br/>''<br/>'
                             'Your  approval  request ' + record.name + ' ' + 'is Delayed by ' +approver.approver_id.name+ '.'
                             'Its escalated to the authority ' + str(record.x_approval_id.user_ids.mapped('partner_id.name')) + ' .'
                             '<br/>''<br/>'
                             '<div style="margin: 16px 0px 16px 0px;">'
                             '<span>'
                             '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href=' + mail_url + '>View Record</a>'
                             '</span>'
                            '</div>'
                            '<br/>''<br/>'
                            'Best regards''<br/>'
                            '</div>'
                            '</td>'
                            '</tr>'
                            '<tr>'
                            '<td style="text-align:center;">'
                            '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                            '</td>'
                            '</tr>'
                            '</table>'
                            '</td>'
                            '</tr>'
                            '<!-- FOOTER -->'
                            '<tr>'
                            '<td align="center" style="min-width: 590px;">'
                            '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                            '<tr>'
                            '<td valign="middle" align="left">'
                            + approver.approver_id.company_id.name +
                            '<br/>'
                            + approver.approver_id.company_id.phone +
                            '</td>'
                            '<td valign="middle" align="right">'
                            '<t t-if="%s" % + approver.approver_id.company_id.email +>'
                            '<a href="mailto:%s % +approver.company_id.email+" style="text-decoration:none; color: #454748;">'
                            + approver.approver_id.company_id.email +
                            '</a>'
                            '</t>'
                            '<br/>'
                            '<t t-if="%s" % + approver.approver_id.company_id.website +>'
                            '<a href="%s % +approver.company_id.website+" style="text-decoration:none; color: #454748;">'
                            + approver.approver_id.company_id.website +
                            '</a>'
                            '</t>'
                            '</td>'
                            '</tr>'
                            '</table>'
                            '</td>'
                            '</tr>'
                            '</tbody>'
                            '</table>'
                    }).send()
                approver.write({'is_send': True})
            for authority in record.x_approval_id.user_ids:
                env['mail.mail'].sudo().create({
                                'subject': record._description + ' Approval Delayed',
                                'author_id': str(approver.approver_id.partner_id.id),
                                'email_from': str(approver.approver_id.login),
                                'email_to':  str(authority.login),
                                'body_html': '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">'
                                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                                        '<tbody>'
                                        '<!-- HEADER -->'
                                        '<tr>'
                                        '<td align="center" style="min-width: 590px;">'
                                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign="middle">'
                                        '<span style="font-size: 10px;">' 'Approval Delayed''</span>''<br/>' +
                                        '<span style="font-size: 20px; font-weight: bold;">' + record.name + '</span>'
                                         '</td>'
                                         '<td valign="middle" align="right">'
                                         '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                         '</td>'
                                         '</tr>'
                                         '<tr>''<td colspan="2" style="text-align:center;">'
                                         '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                         '</td>''</tr>'
                                         '</table>'
                                         '</td>'
                                         '</tr>'
                                         '<!-- CONTENT -->'
                                         '<tr>'
                                         '<td align="center" style="min-width: 590px;">'
                                         '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                         '<tr>'
                                         '<td valign="top" style="font-size: 13px;">'
                                         '<div>'
                                         'Dear' + ' ' + authority.name + ',' '<br/>''<br/>'
                                         'The  approval  request ' + record.name + ' ' + 'is Dealyed by ' +approver.approver_id.name+ '.'
                                         '<br/>''<br/>'
                                         '<div style="margin: 16px 0px 16px 0px;">'
                                         '<span>'
                                         '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href=' + mail_url + '>View Record</a>'
                                         '</span>'
                                        '</div>'
                                        '<br/>''<br/>'
                                        'Best regards''<br/>'
                                        '</div>'
                                        '</td>'
                                        '</tr>'
                                        '<tr>'
                                        '<td style="text-align:center;">'
                                        '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                        '</td>'
                                        '</tr>'
                                        '</table>'
                                        '</td>'
                                        '</tr>'
                                        '<!-- FOOTER -->'
                                        '<tr>'
                                        '<td align="center" style="min-width: 590px;">'
                                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                        '<tr>'
                                        '<td valign="middle" align="left">'
                                        + approver.approver_id.company_id.name +
                                        '<br/>'
                                        + approver.approver_id.company_id.phone +
                                        '</td>'
                                        '<td valign="middle" align="right">'
                                        '<t t-if="%s" + approver.approver_id.company_id.email +>'
                                        '<a href="mailto:%s % +approver.company_id.email+" style="text-decoration:none; color: #454748;">'
                                        + approver.approver_id.company_id.email +
                                        '</a>'
                                        '</t>'
                                        '<br/>'
                                        '<t t-if="%s" % + approver.approver_id.company_id.website +>'
                                        '<a href="%s % +approver.company_id.website+" style="text-decoration:none; color: #454748;">'
                                        + approver.approver_id.company_id.website +
                                        '</a>'
                                        '</t>'
                                        '</td>'
                                        '</tr>'
                                        '</table>'
                                        '</td>'
                                        '</tr>'
                                        '</tbody>'
                                        '</table>'
                                }).send()
            record.write({'x_reminder_mail': True})
            if record.env['ir.model'].search([('model', '=', '""" + model + """')]).is_mail_thread:
                record.message_post(body="Approval request " + record.name + " delayed by " + approver.approver_id.name + "." "Its escalated to the authority" + str(record.x_approval_id.user_ids.mapped('partner_id.name')) + " ." , subject="Approval Request Delayed")
                record.message_post(body="The approval request is delayed and Info mail sent to the created user " + record.create_uid.name+" .", subject="Approval Delayed")
                                """
                            })
        self.multiple_server_action_id = self.check_approval_delay.ir_actions_server_id.id
        stage_id = self.model_id.field_id.filtered(
            lambda l: l.name == 'stage_id')
        if stage_id:
            state_data = []
        else:
            state_data = self.model_states.mapped('value')
        if not self.list_view_id:
            if self.add_approval_status_to_list:
                if self.is_enabled:
                    optional = 'show'
                else:
                    optional = 'hide'
                ids = []
                for rec in self.list_view_name:
                    inherit_list_view_name = rec.name + "_dynamic_approval"
                    # multi_company = self.env['res.users'].has_group(
                    #     'base.group_multi_company')
                    multi_company = self.env.user.has_group('base.group_multi_company')
                    if stage_id:
                        if self.list_field_id:
                            field = self.list_field_id.rec_name
                        else:
                            field = 'stage_id'
                        if multi_company:
                            list_view_arch_base = (_(f'''
                                <data>
                                <xpath expr="//field[@name='{field}']" position="{self.field_position}">
                                <field name="x_approve_state" groups="base.group_multi_company" invisible="company_id not in {str(self.company_id.ids)}"
                                widget="badge" decoration-success="x_approve_state == 'approved'"  optional="{optional}"
                                decoration-info="x_approve_state == 'approve'" decoration-danger="x_approve_state == 'reject'"/>
                                </xpath>
                                </data>'''))
                        else:
                            list_view_arch_base = (_(f'''
                                    <data>
                                    <xpath expr="//field[@name='{field}']" position="{self.field_position}">
                                    <field name="x_approve_state" widget="badge" decoration-success="x_approve_state == 'approved'" optional="{optional}"
                                    decoration-info="x_approve_state == 'approve'" decoration-danger="x_approve_state == 'reject'"/>
                                    </xpath>
                                    </data>'''))
                    else:
                        if self.list_field_id:
                            field = self.list_field_id.rec_name
                        else:
                            field = 'state'
                        if multi_company:
                            list_view_arch_base = (_(f'''
                                <data>
                                <xpath expr="//field[@name='{field}']" position="{self.field_position}">
                                <field name="x_approve_state" groups="base.group_multi_company" invisible="company_id not in {str(self.company_id.ids)}"
                                widget="badge" optional="{optional}" decoration-success="x_approve_state == 'approved'"
                                decoration-info="x_approve_state == 'approve'" decoration-danger="x_approve_state == 'reject'"/>
                                </xpath>
                                </data>'''))
                        else:
                            list_view_arch_base = (_(f'''
                                <data>
                                <xpath expr="//field[@name='{field}']" position="{self.field_position}">
                                <field name="x_approve_state" widget="badge" optional="{optional}" decoration-success="x_approve_state == 'approved'"
                                decoration-info="x_approve_state == 'approve'" decoration-danger="x_approve_state == 'reject'"/>
                        </xpath>
                        </data>'''))
                    s_list_view_id = self.env['ir.ui.view'].sudo().create(
                        {'name': inherit_list_view_name,
                         'type': 'list',
                         'model': self.model_id.model,
                         'mode': 'extension',
                         'inherit_id': rec.id,
                         'arch_base': list_view_arch_base,
                         'active': True})
                    ids.append(s_list_view_id.id)
                self.write({
                    'list_view_id': [(6, 0, ids)],
                })

        if not self.search_view_id:
            if self.add_approval_status_to_list:
                ids = []
                for rec in self.search_view_name:
                    if rec.name:
                        inherit_search_view_name = rec.name + "_dynamic_approval"
                        search_view_arch_base = _(
                            '''<?xml version="1.0"?>'''
                            '''<data>'''
                            '''<xpath expr="//search/group" position="inside">'''
                            '''<filter string="Approved" name="Approved" domain="[('x_approve_state', '=', 'approved')]"/>'''
                            '''<filter string="Waiting For Approval"
                            name="Waiting For Approval" domain="[('x_approve_state', '=', 'approve')]"/>'''
                            '''<filter string="Rejected" name="Rejected" domain="[('x_approve_state', '=', 'reject')]"/>'''
                            '''<filter string="Approver" name="groupby_date" domain="[]" context="{'group_by': 'x_approver_ids'}"/>'''
                            '''</xpath>'''
                            '''</data>''')
                        x_search_view_id = self.env['ir.ui.view'].sudo().create(
                            {'name': inherit_search_view_name,
                             'type': 'search',
                             'model': self.model_id.model,
                             'mode': 'extension',
                             'inherit_id': rec.id,
                             'arch_base': search_view_arch_base,
                             'active': True})
                        ids.append(x_search_view_id.id)
                self.write({
                    'search_view_id': [(6, 0, ids)],
                })

        if not self.view_id:
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                arch_base = (_(f'''
                              <data>
                              <xpath expr="//header" position="after">
                                  <header>
                                      <field name='x_compute' invisible="1"/>
                                      <button name="{str(self.approve_server_action_id.id)}" string="Approve"
                                           class="oe_highlight" type="action"
                                          invisible="x_approve_state in ['reject','approved'] or x_approver_status_checker == False" groups="{group_xml_id}"/>
                                      <button name="{str(self.reject_server_action_id.id)}" string="Reject" class="oe_highlight"
                                          type="action"
                                          invisible="x_approve_state in ['reject', 'approved'] or x_approver_status_checker == False" groups="{group_xml_id}"/>
                                      <button name="{str(self.re_send_server_action_id.id)}" string="Re-Send"
                                          class="oe_highlight" type="action"
                                          invisible="x_approve_state in ['approve', 'approved']"/>
                                      <field name="x_approve_state" widget="statusbar"
                                          statusbar_visible="approved,approve,reject"/>
                                  </header>
                              </xpath>

                              <xpath expr="//sheet" position="inside">
                                  <field name="x_need_to_approve" invisible="1"/>
                                  <field name="x_multi_state" invisible="1"/>
                                  <field name="x_approve_state" invisible="0"/>
                                  <field name="x_compute_one" invisible="1" force_save="1"/>
                                  <field name="x_reminder_mail" invisible="1"/>
                                  <field name="x_check_parllel_approval"
                                  invisible="1"/>
                                  <field name="x_approver_status_checker" invisible="1"/>
                                  <field name="x_header_status_checker" invisible="1"/>
                                  <field name="x_email_status_checker" invisible="1"/>
                                  <field name="x_check_old_records" invisible="1"/>
                                  <field name="x_fully_approved" invisible="1"/>
                                    <notebook invisible="company_id not in {self.company_id.ids}">
                                        <page string="Approves" name="approves">
                                        <field name="x_approval_id" invisible="1" force_save="1" groups="all_in_one_dynamic_approvals_pro.group_all_in_one_dynamic_approval_administrator"/>
                                        <field name="x_approver_ids" mode="list">
                                              <list>
                                              <field name="sequence"/>
                                              <field name="approval_id"/>
                                              <field name="approver_id"/>
                                              <field name="approval_type_id"/>
                                              <field name="approval_status"/>
                                              <field name="approve_stage_id"/>
                                              <field name="approval_email_status"/>
                                              <field name="reject_reason"/>
                                              <field name="time_limit" widget="float_time"/>
                                              <field name="delay" invisible="1"/>
                                              <field name="authority_email_status"/>
                                              <field name="is_send" invisible="1"/>
                                              <field name="approval_duration"/>
                                              <field name="start_date" invisible="1"/>
                                              <field name="end_date" invisible="1"/>
                                              </list>
                                              <form create="false" edit="false" delete="false">
                                              <group>
                                              <group>
                                              <field name="sequence" readonly="1"/>
                                              <field name="approval_id" readonly="1"/>
                                              <field name="approver_id" readonly="1"/>
                                              <field name="approval_status" readonly="1"/>
                                              <field name="approval_email_status" readonly="1"/>
                                              <field name="reject_reason" readonly="1"/>
                                              </group>
                                              <group>
                                              <field name="approve_stage_id"/>
                                              <field name="time_limit" widget="float_time" readonly="1"/>
                                              <field name="delay" readonly="1"/>
                                              <field name="authority_email_status" readonly="1"/>
                                              <field name="is_send" invisible="1" readonly="1"/>
                                              field name="approval_duration" readonly="1"/>
                                              <field name="start_date" invisible="1" readonly="1"/>
                                              <field name="end_date" invisible="1" readonly="1"/>
                                              </group>
                                              </group>
                                              <footer>
                                              <button string="Cancel" special="cancel"/>
                                              </footer>
                                              </form>
                                        </field>
                                        </page>
                                      </notebook>
                              </xpath>
                              <xpath expr="//form/header[1]" position="attributes">
                                    <attribute name="invisible">x_need_to_approve == True and  company_id in {self.company_id.ids} or x_header_status_checker == True</attribute>
                              </xpath>
                              <xpath expr="//form/header[2]" position="attributes">
                                    <attribute name="invisible">x_multi_state != True or company_id not in {self.company_id.ids} or x_header_status_checker == False</attribute>
                              </xpath>
                    </data>'''))
            else:
                arch_base = (_(f'''
                <data>
                <xpath expr="//header" position="after">
                <header>
                    <field name='x_compute' invisible="1"/>

                    <button name="{str(self.approve_server_action_id.id)}" string="Approve" class="oe_highlight" type="action"
                        invisible="x_approve_state in ['reject','approved'] or x_approver_status_checker == False" groups="{group_xml_id}"/>

                    <button name="{str(self.reject_server_action_id.id)}" string="Reject" class="oe_highlight" type="action"
                        invisible="x_approve_state in ['reject', 'approved'] or x_approver_status_checker == False" groups="{group_xml_id}"/>

                    <button name="{str(self.re_send_server_action_id.id)}" string="Re-Send" class="oe_highlight" type="action"
                        invisible="x_approve_state in ['approve', 'approved']"/>
                x_compute
                    <field name="x_approve_state" widget="statusbar"
                        statusbar_visible="approved,approve,reject"/>
                </header>
                </xpath>

                <xpath expr="//sheet" position="inside">
                <field name="x_need_to_approve" invisible="1"/>
                <field name="x_multi_state" invisible="1"/>
                <field name="x_approve_state" invisible="1"/>
                <field name="x_compute_one" invisible="1" force_save="1"/>
                <field name="x_reminder_mail" invisible="1"/>
                <field name="x_check_parllel_approval" invisible="1"/>
                <field name="x_approver_status_checker" invisible="1"/>
                <field name="x_header_status_checker" invisible="1"/>
                <field name="x_email_status_checker" invisible="1"/>
                <field name="x_check_old_records" invisible="1"/>
                <field name="x_fully_approved" invisible="1"/>

                <notebook invisible="company_id not in {self.company_id.ids}">
                    <page string="Approves" name="approves">
                        <field name="x_approval_id" invisible="1" force_save="1" groups="all_in_one_dynamic_approvals_pro.group_all_in_one_dynamic_approval_administrator"/>
                        <field name="x_approver_ids" mode="list">
                            <list>
                                <field name="sequence"/>
                                <field name="approval_id"/>
                                <field name="approver_id"/>
                                <field name="approval_type_id"/>
                                <field name="approval_status"/>
                                <field name="approve_state"/>
                                <field name="approval_email_status"/>
                                <field name="reject_reason" optional="hide"/>/>
                                <field name="time_limit" widget="float_time"/>
                                <field name="delay" invisible="1"/>
                                <field name="authority_email_status"/>
                                <field name="is_send" optional="hide"/>
                                <field name="approval_duration" optional="hide"/>
                                <field name="start_date" optional="hide"/>
                                <field name="end_date" optional="hide"/>
                            </list>
                            <form create="false" edit="false" delete="false">
                                <group>
                                    <group>
                                        <field name="sequence" readonly="1"/>
                                        <field name="approval_id" readonly="1"/>
                                        <field name="approver_id" readonly="1"/>
                                        <field name="approval_status" readonly="1"/>
                                        <field name="approval_email_status" readonly="1"/>
                                        <field name="reject_reason" readonly="1"/>
                                        <field name="approve_state" readonly="1"/>
                                    </group>
                                    <group>
                                        <field name="time_limit" widget="float_time" readonly="1"/>
                                        <field name="delay" readonly="1"/>
                                        <field name="authority_email_status" readonly="1"/>
                                        <field name="is_send" invisible="1" readonly="1"/>
                                        <field name="approval_duration" readonly="1"/>
                                        <field name="start_date" invisible="1" readonly="1"/>
                                        <field name="end_date" invisible="1" readonly="1"/>
                                    </group>
                                </group>
                                <footer>
                                    <button string="Cancel" special="cancel"/>
                                </footer>
                            </form>
                        </field>
                    </page>
                </notebook>
                </xpath>
                    <xpath expr="//form/header[1]" position="attributes">
                    <attribute name="invisible">state in {state_data} and  x_need_to_approve == True and company_id in {self.company_id.ids} or x_header_status_checker == True</attribute>
                </xpath>
                    <xpath expr="//form/header[2]" position="attributes">
                    <attribute name="invisible">state not in {state_data} or x_multi_state != True or company_id not in {self.company_id.ids} or x_header_status_checker == False</attribute>
                </xpath>
            </data>
                    '''
                               ))
            self.view_id = self.env['ir.ui.view'].sudo().create(
                {'name': inherit_name,
                 'type': 'form',
                 'model': self.model_id.model,
                 'mode': 'extension',
                 'inherit_id': inherit_id.id,
                 'arch_base': arch_base,
                 'active': True})
            cr = self.env.cr
            table_name = self.model_id.model.replace('.', '_')
            sql = """update  %s set x_check_old_records = %s """ % (
                str(table_name), True)
            cr.execute(sql)

            for record in self.action_id:
                uid = self.env.user.id
                for rec in record:
                    if rec.context:
                        opening_brace_index = rec.context.find('{')
                        if opening_brace_index != -1:
                            updated_dict_str = (
                                    rec.context[:opening_brace_index + 1] +
                                    f" 'default_x_need_to_approve': False,"
                                    f"'default_x_multi_state': True,"
                                    f"'default_company_id':{self.env.company.id},"
                                    f"'default_{self.approval_id.name}': {self.id},"
                                    f"'default_x_approve_state': 'approve'," +
                                    rec.context[opening_brace_index + 1:])
                        else:
                            updated_dict_str = (
                                    "{" +
                                    f" 'default_x_need_to_approve': False,"
                                    f"'default_x_multi_state': True,"
                                    f"'default_company_id':{self.env.company.id},"
                                    f"'default_{self.approval_id.name}': {self.id},"
                                    f"'default_x_approve_state': 'approve',"
                                    f"{rec.context}")
                        rec.write({'context': updated_dict_str})
                    else:
                        raise UserError(
                            _("You chose a model, but we can't create Approval because the model doesn't have the Context."))
        self.write({'state': 'active'})
        self.model_id.is_approval = True
        for each in self.record_ids:
            each.save = True
        for each in self.list_field_id:
            each.save = True
        stage_id = self.model_id.field_id.filtered(
            lambda l: l.name == 'stage_id')
        if self.state_specific_approval:
            automation_action_name = self.model_id.name + ' Automate Action Change'
            status = self.compute_one
            if not self.automation_action_id:
                automation_server_action_id = self.env['ir.actions.server']. \
                    sudo().create([
                    {
                        'update_field_id': self.approve_state_id.id,
                        'evaluation_type': 'value',
                        'update_path': self.approve_state_id.name,
                        'name': self.approve_state_id.field_description,
                        'model_id': self.model_id.id,
                        'usage': 'ir_actions_server',
                        'state': 'object_write',
                        'value': 'approve'
                    }])
                self.automation_action_id = self.env['base.automation'].sudo(). \
                    create({'name': "State Specific" + automation_action_name,
                            'model_id': self.model_id.id,
                            'active': True,
                            'trigger': 'on_write',
                            'trigger_field_ids': status,
                            'action_server_ids': automation_server_action_id,
                            })
        if stage_id:
            automation_action_name = self.model_id.name + ' Automate Action Change'
            status = self.compute_one
            automation_server_action_id = self.env['ir.actions.server']. \
                sudo().create([
                {
                    'update_field_id': self.need_to_approve_id.id,
                    'update_path': self.need_to_approve_id.name,
                    'name': self.need_to_approve_id.field_description,
                    'model_id': self.model_id.id,
                    'usage': 'ir_actions_server',
                    'state': 'code',
                    'code': """
            for record in records:
                if record.x_approval_id.record_ids:
                  if str(record.stage_id.id) in record.x_approval_id.record_ids[0].rec_id:
                    record.update({'x_need_to_approve': True})""",
                }])
            if not self.automation_action_id_three:
                domain = "[('x_need_to_approve', '=', True)]"
                self.automation_action_id_three = self.env[
                    'base.automation'].sudo(). \
                    create({'name': automation_action_name + ' warning',
                            'model_id': self.model_id.id,
                            'active': True,
                            'trigger': 'on_write',
                            'trigger_field_ids': status,
                            'filter_pre_domain': domain,
                            'filter_domain': domain,
                            'action_server_ids': automation_server_action_id,
                            })
            stage_id = self.model_id.field_id.filtered(
                lambda l: l.name == 'stage_id')
            if stage_id:
                automation_server_action_id = self.env['ir.actions.server']. \
                    sudo().create([
                    {
                        'update_field_id': self.need_to_approve_id.id,
                        'update_path': self.need_to_approve_id.name,
                        'name': self.need_to_approve_id.field_description,
                        'model_id': self.model_id.id,
                        'usage': 'ir_actions_server',
                        'state': 'code',
                        'code': "raise UserError('Record Not Approved !')",
                    }])
                if not self.automation_action_id_two:
                    domain = "[('x_need_to_approve', '=', True)]"
                    self.automation_action_id_two = self.env[
                        'base.automation'].sudo(). \
                        create({'name': automation_action_name + ' warning',
                                'model_id': self.model_id.id,
                                'active': True,
                                'trigger': 'on_write',
                                'trigger_field_ids': status,
                                'filter_pre_domain': domain,
                                'filter_domain': domain,
                                'action_server_ids': automation_server_action_id,
                                })
                automation_server_action_id = self.env['ir.actions.server']. \
                    sudo().create([
                    {
                        'name': 'Approves link to group Automation',
                        'model_id': self.model_id.id,
                        'usage': 'ir_actions_server',
                        'state': 'code',
                        'code': """
            for rec in record:
                if rec.x_approval_id.approval_method == 'hierarchy':
                    for lines in rec.x_approver_ids:
                        if lines.approver_id:
                            rec.x_approval_id.group_id.write({'user_ids': [(4,lines.approver_id.id,0)]})""",
                    }])
                if not self.approves_automation_action_id:
                    self.approves_automation_action_id = self.env[
                        'base.automation'].sudo().create({
                        'name': 'Approves link to group Automation ',
                        'model_id': self.model_id.id,
                        'active': True,
                        'trigger': 'on_create_or_write',
                        'trigger_field_ids': self.approver_ids,
                        'action_server_ids': automation_server_action_id
                    })
        if not self.state_specific_approves_automation_id:
            automation_server_action_id = self.env['ir.actions.server']. \
                sudo().create([
                {
                    'name': self.need_to_approve_id.field_description,
                    'model_id': self.model_id.id,
                    'usage': 'ir_actions_server',
                    'state': 'code',
                    'code': """
            if record.x_approver_ids and record.id:
                for rec in record.x_approver_ids:
                    if rec.approver_id:
                        if rec.approver_id.id not in record.x_approval_id.group_id.user_ids.mapped('id'):
                            record.x_approval_id.group_id.write({'user_ids': [(4,rec.approver_id.id,0)]})
                    """,
                }])
            self.state_specific_approves_automation_id = self.env[
                'base.automation'].sudo().create({
                'name': 'Automated x_approve set',
                'model_id': self.model_id.id,
                'active': True,
                'trigger': 'on_create_or_write',
                'trigger_field_ids': [self.model_id.field_id.filtered(
                    lambda
                        l: l.name == 'state').id] if self.model_id.field_id.filtered(
                    lambda l: l.name == 'state') else [
                    self.model_id.field_id.filtered(
                        lambda l: l.name == 'stage_id').id],
                'action_server_ids': [automation_server_action_id.id]
            })

        if self.env['ir.config_parameter'].sudo().get_param(
                'all_in_one_dynamic_approvals_pro.is_notify_approval_add'):
            data = {
                'table_data': "no",
                'self': self,
                'company_name': ', '.join(self.company_id.mapped('name')),
                'created': self.env.user,
                'created_date': self.create_date.strftime('%Y-%m-%d'),
                'cancelled_date': datetime.now().strftime('%Y-%m-%d'),
                'Action': ', '.join(self.action_id.mapped('name')),
            }
            approval_report_pdf = self.env.ref(
                'all_in_one_dynamic_approvals_pro.all_in_one_dynamic_approvals_pro_report_action')
            data_values = base64.b64encode(
                self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                    approval_report_pdf, data=data)[0])
            ir_values = {
                'name': "Dynamic Approval Create Report",
                'type': 'binary',
                'datas': data_values,
                'store_fname': data_values,
                'mimetype': 'application/x-pdf',
                'res_model': 'dynamic.approval',
            }
            data_id = self.env['ir.attachment'].create(ir_values)
            template = self.env.ref(
                'all_in_one_dynamic_approvals_pro.mail_template_dynamic_approval')
            template.attachment_ids = data_id
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip('/')

            mail_url = base_url + '/odoo/' + str(self._name) + '/' + str(self.id)
            for user in eval(self.env['ir.config_parameter'].sudo().get_param(
                    'all_in_one_dynamic_approvals_pro.add_notify_users_ids')):
                user_id = self.env['res.users'].browse(user)
                email_values = {
                    'subject': f"""{self.model_id.name} Approval Created""",
                    'email_to': user_id.email,
                    'body_html':
                        '<table border=0 cellpadding=0 cellspacing=0 '
                        'style="padding-top: 16px; background-color: '
                        '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                        'color: #454748; width: 100%; '
                        'border-collapse:separate;"><tr><td align=center>'
                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                        '<tbody>'
                        '<!-- HEADER -->'
                        '<tr>'
                        '<td align=center style="min-width: 590px;">'
                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                        '<tr>'
                        '<td valign=middle>'
                        '<span style="font-size: 10px;">Approval Created</span><br/>'
                        '<span style="font-size: 20px; font-weight: bold;">' +
                        f"""{self.name}"""
                        + '</span>'
                          '</td>'
                          '<td valign=middle align=right>'
                          '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                          '</td>'
                          '</tr>'
                          '<tr><td colspan=2 style="text-align:center;">'
                          '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                          '</td></tr>'
                          '</table>'
                          '</td>'
                          '</tr>'
                          '<!-- CONTENT -->'
                          '<tr>'
                          '<td align=center style="min-width: 590px;">'
                          '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                          '<tr>'
                          '<td valign=top style="font-size: 13px;">'
                          '<div>'
                          'Hi ' +
                        f"""{user_id.name}"""
                        ',<br/><br/>'
                        f""" Approval {self.approval_name} has been Created """ + '.<br/><br/>'
                                                                                  f""" For your information please find the attachment """ + '<br/><br/>'
                                                                                                                                             '<span style="color: red;">'
                                                                                                                                             f"""{self.approval_name} has been Created by {self.env.user.name}"""
                                                                                                                                             '</span>'
                                                                                                                                             '<br/><br/>'
                                                                                                                                             '<div style="margin: 16px 0px 16px 0px;">'
                                                                                                                                             '<span>'
                                                                                                                                             '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href=' + f"""{mail_url}""" + '>View Record</a>'
                                                                                                                                                                                                                                                                                                                     '</span>'
                                                                                                                                                                                                                                                                                                                     '</div>'
                                                                                                                                                                                                                                                                                                                     '<br/><br/>Best regards<br/>'
                                                                                                                                                                                                                                                                                                                     '</div>'
                                                                                                                                                                                                                                                                                                                     '</td>'
                                                                                                                                                                                                                                                                                                                     '</tr>'
                                                                                                                                                                                                                                                                                                                     '<tr>'
                                                                                                                                                                                                                                                                                                                     '<td style="text-align:center;">'
                                                                                                                                                                                                                                                                                                                     '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                                                                                                                                                                                                                                                                                     '</td>'
                                                                                                                                                                                                                                                                                                                     '</tr>'
                                                                                                                                                                                                                                                                                                                     '</table>'
                                                                                                                                                                                                                                                                                                                     '</td>'
                                                                                                                                                                                                                                                                                                                     '</tr>'
                                                                                                                                                                                                                                                                                                                     '<!-- FOOTER -->'
                                                                                                                                                                                                                                                                                                                     '<tr>'
                                                                                                                                                                                                                                                                                                                     '<td align=center style="min-width: 590px;">'
                                                                                                                                                                                                                                                                                                                     '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                                                                                                                                                                                                                                                                                     '<tr>'
                                                                                                                                                                                                                                                                                                                     '<td valign=middle align=left>'
                        + f"""{self.env.user.company_id.name}""" +
                        '<br/>'
                        + f"""{self.env.user.company_id.phone}""" +
                        '</td>'
                        '<td valign=middle align=right>'
                        '<t t-if="%s" % +user_id.company_id.email>'
                        '<a href="mailto:%s % +user_id.company_id.email+" style="text-decoration:none; color: #535556;">'
                        + f"""{self.env.user.company_id.email}""" +
                        '</a>'
                        '</t>'
                        '<br/>'
                        '<t t-if="%s % +user_id.company_id.website+ ">'
                        '<a href="%s % +user_id.company_id.website+" style="text-decoration:none; color: #535556;">'
                        + f"""{self.env.user.company_id.website}""" +
                        '</a>'
                        '</t>'
                        '</td>'
                        '</tr>'
                        '</table>'
                        '</td>'
                        '</tr>'
                        '</tbody>'
                        '</table>'
                        '</td>'
                        '</tr>'
                        '</table>'
                }
                template.send_mail(self.id, email_values=email_values,
                                   force_send=True)
            if self.env['ir.model'].search(
                    [('model', '=', self._name)]).is_mail_thread:
                self.message_post(
                    body=self._description + " for " + self.approval_name + " is Created by " + self.env.user.name,
                    subject="Approval Created")

    def set_draft_button(self):
        """Set the current approval to draft state"""
        self.state = 'draft'

    def allow_multi_state_approval(self):
        """Button function of allow multi state approval"""
        self.multi_state_enabled = True
        self.automation_action_id_two.sudo().unlink()
        self.automation_action_id_three.sudo().unlink()
        self.automation_action_id.sudo().unlink()
        self.write({'state': 'multi_state_activated'})
        self.message_post(body="Multi State Approval Activated",
                          subject="Multi State Approval")
        automation_action_name = self.model_id.name + ' Automate Action Change'
        status = self.compute_one
        if not self.automation_action_id:
            automation_server_action_id = self.env['ir.actions.server']. \
                sudo().create([
                {
                    'update_field_id': self.multi_state_field_id.id,
                    'evaluation_type': 'value',
                    'update_path': self.multi_state_field_id.name,
                    'name': self.multi_state_field_id.field_description,
                    'model_id': self.model_id.id,
                    'usage': 'ir_actions_server',
                    'state': 'object_write',
                    'value': 'True'
                },
                {
                    'update_field_id': self.approve_state_id.id,
                    'evaluation_type': 'value',
                    'update_path': self.approve_state_id.name,
                    'name': self.approve_state_id.field_description,
                    'model_id': self.model_id.id,
                    'usage': 'ir_actions_server',
                    'state': 'object_write',
                    'value': 'approve'
                }])
            self.automation_action_id = self.env['base.automation'].sudo(). \
                create({'name': automation_action_name,
                        'model_id': self.model_id.id,
                        'active': True,
                        'trigger': 'on_write',
                        'trigger_field_ids': status,
                        'action_server_ids': automation_server_action_id,
                        })
        automation_server_action_id = self.env['ir.actions.server']. \
            sudo().create([
            {
                'update_field_id': self.need_to_approve_id.id,
                'update_path': self.need_to_approve_id.name,
                'name': self.need_to_approve_id.field_description,
                'model_id': self.model_id.id,
                'usage': 'ir_actions_server',
                'state': 'code',
                'code': """
for record in records:
    if record.x_approval_id.record_ids:
      if str(record.stage_id.id) in record.x_approval_id.record_ids.mapped('rec_id'):
        record.update({'x_need_to_approve': True})""",
            }])

        if not self.automation_action_id_three:
            domain = "[('x_need_to_approve', '=', True)]"
            self.automation_action_id_three = self.env[
                'base.automation'].sudo(). \
                create({'name': automation_action_name + ' warning',
                        'model_id': self.model_id.id,
                        'active': True,
                        'trigger': 'on_write',
                        'trigger_field_ids': status,
                        'filter_pre_domain': domain,
                        'filter_domain': domain,
                        'action_server_ids': automation_server_action_id,
                        })
        stage_id = self.model_id.field_id.filtered(
            lambda l: l.name == 'stage_id')
        if stage_id:
            automation_server_action_id = self.env['ir.actions.server']. \
                sudo().create([
                {
                    'update_field_id': self.need_to_approve_id.id,
                    'update_path': self.need_to_approve_id.name,
                    'name': self.need_to_approve_id.field_description,
                    'model_id': self.model_id.id,
                    'usage': 'ir_actions_server',
                    'state': 'code',
                    'code': "raise UserError('Record Not Approved !')",
                }])
            if not self.automation_action_id_two:
                domain = "[('x_need_to_approve', '=', True)]"
                self.automation_action_id_two = self.env[
                    'base.automation'].sudo(). \
                    create({'name': automation_action_name + ' warning',
                            'model_id': self.model_id.id,
                            'active': True,
                            'trigger': 'on_write',
                            'trigger_field_ids': status,
                            'filter_pre_domain': domain,
                            'filter_domain': domain,
                            'action_server_ids': automation_server_action_id,
                            })

    def apply_old_record(self):
        """Button function of apply for old record"""
        self.apply_old_records = True
        approval_id = self.env['dynamic.approval'].search(
            [('model_id', '=', self.model_id.model)]).id
        cr = self.env.cr
        table_name = self.model_id.model.replace('.', '_')
        sql = """update  %s set x_need_to_approve = %s, x_multi_state = %s, x_approval_id = %s, x_approve_state = '%s'
        WHERE x_check_old_records = %s """ % (
            str(table_name), True, True, str(approval_id), str('approve'), True)
        cr.execute(sql)
        self.write({'state': 'old'})
        records = self.env[self.model_id.model].search([])
        for rec in records:
            rec.write({'x_compute': True})
        self.message_post(body="Approval applied to Old records",
                          subject="Applied to Old Records")

    def update_approvers_list(self):
        """Button function to update the created approval request"""
        self.write({'state': 'update'})
        self.message_post(body="Need To Change Approvers List",
                          subject="Approvers List")

    def apply_changes(self):
        """Apply Changes in the Updated approval request"""
        self.write({'state': 'apply'})
        self.message_post(body="The Approves List Updated",
                          subject="Approvers List")

    def unlink(self):
        """Function unlink"""
        reports_data = self.env['ir.actions.report'].search(
            [('model', '=', self.model_id.model)])
        reports_data.create_action()
        self.view_id.sudo().unlink()
        self.list_view_id.sudo().unlink()
        self.search_view_id.sudo().unlink()
        self.automation_action_id_two.sudo().unlink()
        self.automation_action_id_three.sudo().unlink()
        self.state_specific_approves_automation_id.sudo().unlink()
        self.approves_automation_action_id.sudo().unlink()
        self.automation_action_id.action_server_ids.sudo().unlink()
        self.automation_action_id.sudo().unlink()
        self.approve_server_action_id.sudo().unlink()
        self.reject_server_action_id.sudo().unlink()
        self.re_send_server_action_id.sudo().unlink()
        self.custom_field_id.sudo().unlink()
        self.approve_state_id.sudo().unlink()
        self.reject_reason_id.sudo().unlink()
        self.need_to_approve_id.sudo().unlink()
        self.parallel_approval_duration_id.sudo().unlink()
        self.multi_state_field_id.sudo().unlink()
        self.email_template_id.sudo().unlink()
        self.email_template_server_action_id.sudo().unlink()
        self.approve_server_action_id.sudo().unlink()
        self.fully_approved_field_id.depends = False
        self.fully_approved_field_id.sudo().unlink()
        self.multi_approver_status_checker_id.depends = False
        self.multi_approver_status_checker_id.sudo().unlink()
        self.header_status_checker.depends = False
        self.header_status_checker.sudo().unlink()
        self.email_status_checker_id.depends = False
        self.email_status_checker_id.sudo().unlink()
        self.check_old_records_id.sudo().unlink()
        self.reminder_mail.sudo().unlink()
        self.approver_ids.depends = False
        self.group_id.sudo().unlink()
        self.approval_id.sudo().unlink()
        self.approver_ids.sudo().unlink()
        self.compute_approve.sudo().unlink()
        self.compute_one.depends = False
        self.compute_one.sudo().unlink()
        self.approval_model.sudo().unlink()
        self.check_approval_delay.sudo().unlink()
        self.multiple_server_action_id.sudo().unlink()
        self.model_id.is_approval = False
        return super(Approval, self).unlink()

    def action_approval_cancel(self):
        state_records = {}
        if self.check_states_type:
            for state in self.record_ids:
                state_records[state.rec_name] = str(
                    self.env[self.model_id.model].search_count(
                        [('x_approval_id', '!=', False),
                         ('x_approve_state', '=',
                          'approve'),
                         ('stage_id.name', '=', state.rec_name)]))
        else:
            for state in self.model_states:
                state_records[state.value] = str(
                    self.env[self.model_id.model].search_count(
                        [('x_approval_id', '!=', False),
                         ('x_approve_state', '=',
                          'approve'),
                         ('state', '=', state.value)]))
        self.multi_state_enabled = False
        self.apply_old_records = False
        reports_data = self.env['ir.actions.report'].search(
            [('model', '=', self.model_id.model)])
        reports_data.create_action()
        self.view_id.sudo().unlink()
        self.list_view_id.sudo().unlink()
        self.search_view_id.sudo().unlink()
        self.automation_action_id_two.sudo().unlink()
        self.state_specific_approves_automation_id.sudo().unlink()
        self.automation_action_id_three.sudo().unlink()
        self.approves_automation_action_id.sudo().unlink()
        self.automation_action_id.action_server_ids.sudo().unlink()
        self.automation_action_id.sudo().unlink()
        self.approve_server_action_id.sudo().unlink()
        self.reject_server_action_id.sudo().unlink()
        self.re_send_server_action_id.sudo().unlink()
        self.custom_field_id.sudo().unlink()
        self.approve_state_id.sudo().unlink()
        self.reject_reason_id.sudo().unlink()
        self.need_to_approve_id.sudo().unlink()
        self.parallel_approval_duration_id.sudo().unlink()
        self.multi_state_field_id.sudo().unlink()
        self.email_template_id.sudo().unlink()
        self.email_template_server_action_id.sudo().unlink()
        self.approve_server_action_id.sudo().unlink()
        self.fully_approved_field_id.depends = False
        self.fully_approved_field_id.sudo().unlink()
        self.multi_approver_status_checker_id.depends = False
        self.multi_approver_status_checker_id.sudo().unlink()
        self.header_status_checker.depends = False
        self.header_status_checker.sudo().unlink()
        self.email_status_checker_id.depends = False
        self.email_status_checker_id.sudo().unlink()
        self.check_old_records_id.sudo().unlink()
        self.reminder_mail.sudo().unlink()
        self.approver_ids.depends = False
        self.group_id.sudo().unlink()
        self.approval_id.sudo().unlink()
        self.approver_ids.sudo().unlink()
        self.compute_approve.sudo().unlink()
        self.compute_one.depends = False
        self.compute_one.sudo().unlink()
        self.approval_model.sudo().unlink()
        self.check_approval_delay.sudo().unlink()
        self.multiple_server_action_id.sudo().unlink()
        self.model_id.is_approval = False
        self.write({'state': 'cancel'})
        if self.env['ir.config_parameter'].sudo().get_param(
                'all_in_one_dynamic_approvals_pro.is_notify_approval_cancel'):
            data = {
                'table_data': state_records,
                'self': self,
                'company_name': ', '.join(self.company_id.mapped('name')),
                'cancelled': self.env.user,
                'created_date': self.create_date.strftime('%Y-%m-%d'),
                'cancelled_date': datetime.now().strftime('%Y-%m-%d'),
                'Action': ', '.join(self.action_id.mapped('name')),
            }
            approval_report_pdf = self.env.ref(
                'all_in_one_dynamic_approvals_pro.all_in_one_dynamic_approvals_pro_report_action')
            data_values = base64.b64encode(
                self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                    approval_report_pdf, data=data)[0])
            ir_values = {
                'name': "Dynamic Approval Cancel Report",
                'type': 'binary',
                'datas': data_values,
                'store_fname': data_values,
                'mimetype': 'application/x-pdf',
                'res_model': 'dynamic.approval',
            }
            data_id = self.env['ir.attachment'].create(ir_values)
            template = self.env.ref(
                'all_in_one_dynamic_approvals_pro.mail_template_dynamic_approval')
            template.attachment_ids = data_id
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip('/')
            mail_url = base_url + '/odoo/' + str(self._name) + '/' + str(self.id)
            for user in eval(self.env['ir.config_parameter'].sudo().get_param(
                    'all_in_one_dynamic_approvals_pro.cancel_notify_users_ids')):
                user_id = self.env['res.users'].browse(user)
                email_values = {
                    'subject': f"""{self.model_id.name} Approval Canceled""",
                    'email_to': user_id.email,
                    'body_html':
                        '<table border=0 cellpadding=0 cellspacing=0 '
                        'style="padding-top: 16px; background-color: '
                        '#F1F1F1; font-family:Verdana, Arial,sans-serif; '
                        'color: #454748; width: 100%; '
                        'border-collapse:separate;"><tr><td align=center>'
                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                        '<tbody>'
                        '<!-- HEADER -->'
                        '<tr>'
                        '<td align=center style="min-width: 590px;">'
                        '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                        '<tr>'
                        '<td valign=middle>'
                        '<span style="font-size: 10px;">Approval Canceled</span><br/>'
                        '<span style="font-size: 20px; font-weight: bold;">' +
                        f"""{self.name}"""
                        + '</span>'
                          '</td>'
                          '<td valign=middle align=right>'
                          '<img src="/logo.png?company=" + record.company_id.id + style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                          '</td>'
                          '</tr>'
                          '<tr><td colspan=2 style="text-align:center;">'
                          '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                          '</td></tr>'
                          '</table>'
                          '</td>'
                          '</tr>'
                          '<!-- CONTENT -->'
                          '<tr>'
                          '<td align=center style="min-width: 590px;">'
                          '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                          '<tr>'
                          '<td valign=top style="font-size: 13px;">'
                          '<div>'
                          'Hi ' +
                        f"""{user_id.name}"""
                        ',<br/><br/>'
                        f""" Approval {self.approval_name} has been Canceled """ + '.<br/><br/>'
                                                                                   f""" For your information please find the attachment """ + '<br/><br/>'
                                                                                                                                              '<span style="color: red;">'
                                                                                                                                              f"""{self.approval_name} has been cancelled by {self.env.user.name}"""
                                                                                                                                              '</span>'
                                                                                                                                              '<br/><br/>'
                                                                                                                                              '<div style="margin: 16px 0px 16px 0px;">'
                                                                                                                                              '<span>'
                                                                                                                                              '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href=' + f"""{mail_url}""" + '>View Record</a>'
                                                                                                                                                                                                                                                                                                                      '</span>'
                                                                                                                                                                                                                                                                                                                      '</div>'
                                                                                                                                                                                                                                                                                                                      '<br/><br/>Best regards<br/>'
                                                                                                                                                                                                                                                                                                                      '</div>'
                                                                                                                                                                                                                                                                                                                      '</td>'
                                                                                                                                                                                                                                                                                                                      '</tr>'
                                                                                                                                                                                                                                                                                                                      '<tr>'
                                                                                                                                                                                                                                                                                                                      '<td style="text-align:center;">'
                                                                                                                                                                                                                                                                                                                      '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                                                                                                                                                                                                                                                                                      '</td>'
                                                                                                                                                                                                                                                                                                                      '</tr>'
                                                                                                                                                                                                                                                                                                                      '</table>'
                                                                                                                                                                                                                                                                                                                      '</td>'
                                                                                                                                                                                                                                                                                                                      '</tr>'
                                                                                                                                                                                                                                                                                                                      '<!-- FOOTER -->'
                                                                                                                                                                                                                                                                                                                      '<tr>'
                                                                                                                                                                                                                                                                                                                      '<td align=center style="min-width: 590px;">'
                                                                                                                                                                                                                                                                                                                      '<table border=0 cellpadding=0 cellspacing=0 width=590 style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                                                                                                                                                                                                                                                                                      '<tr>'
                                                                                                                                                                                                                                                                                                                      '<td valign=middle align=left>'
                        + f"""{self.env.user.company_id.name}""" +
                        '<br/>'
                        + f"""{self.env.user.company_id.phone}""" +
                        '</td>'
                        '<td valign=middle align=right>'
                        '<t t-if="%s" % +user_id.company_id.email>'
                        '<a href="mailto:%s % +user_id.company_id.email+" style="text-decoration:none; color: #535556;">'
                        + f"""{self.env.user.company_id.email}""" +
                        '</a>'
                        '</t>'
                        '<br/>'
                        '<t t-if="%s % +user_id.company_id.website+ ">'
                        '<a href="%s % +user_id.company_id.website+" style="text-decoration:none; color: #535556;">'
                        + f"""{self.env.user.company_id.website}""" +
                        '</a>'
                        '</t>'
                        '</td>'
                        '</tr>'
                        '</table>'
                        '</td>'
                        '</tr>'
                        '</tbody>'
                        '</table>'
                        '</td>'
                        '</tr>'
                        '</table>'
                }
                template.send_mail(self.id, email_values=email_values,
                                   force_send=True)
            if self.env['ir.model'].search(
                    [('model', '=', self._name)]).is_mail_thread:
                self.message_post(
                    body=self._description + " for " + self.approval_name + " is canceled by " + self.env.user.name,
                    subject="Approval Canceled")
