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
from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    """Inherits the Configuration Settings Model"""
    _inherit = "res.config.settings"
    _description = "Inherited res.config.settings for additional features"

    approval_type = fields.Boolean(string='Approval type',
                                   config_parameter="all_in_one_dynamic_approvals_pro.approval_type",
                                   help='if enabled approval is '
                                        'approved by managers of '
                                        'respective person',
                                   implied_group='all_in_one_dynamic_approvals_pro.approval_type')
    is_notify_approval_cancel = fields.Boolean(string='Notify Approval Cancel',
                                               config_parameter="all_in_one_dynamic_approvals_pro.is_notify_approval_cancel",
                                               help='If enabled Email notifications will be sent to assigned users on cancellation of approval',
                                               implied_group='all_in_one_dynamic_approvals_pro.approval_type'
                                               )
    is_notify_approval_add = fields.Boolean(string='Notify Approval Creation',
                                               config_parameter="all_in_one_dynamic_approvals_pro.is_notify_approval_add",
                                               help='If enabled Email notifications will be sent to assigned users on creation of approval',
                                               implied_group='all_in_one_dynamic_approvals_pro.approval_type'
                                               )
    cancel_notify_users_ids = fields.Many2many('res.users',
                                        string='Users to notify on approval cancel',
                                        help="Email notifications to this "
                                             "users will be sent on cancel of "
                                             "approval")
    add_notify_users_ids = fields.Many2many('res.users', 'notify_created_users_table',
                                               string='Users to notify on approval creation',
                                               help="Email notifications to this "
                                                    "users will be sent on cancel of "
                                                    "approval")

    def set_values(self):
        """this function helps to save values in the settings"""
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'all_in_one_dynamic_approvals_pro.cancel_notify_users_ids',
            self.cancel_notify_users_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param(
            'all_in_one_dynamic_approvals_pro.add_notify_users_ids',
            self.add_notify_users_ids.ids)
        return res

    @api.model
    def get_values(self):
        """this function retrieve the values from the ir_config_parameters"""
        res = super().get_values()
        cancel_notify_users_ids = self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_dynamic_approvals_pro.cancel_notify_users_ids')
        add_notify_users_ids = self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_dynamic_approvals_pro.add_notify_users_ids')
        res.update(
            cancel_notify_users_ids=[
                fields.Command.set(literal_eval(cancel_notify_users_ids))
            ] if cancel_notify_users_ids else False)
        res.update(
            add_notify_users_ids=[
                fields.Command.set(literal_eval(add_notify_users_ids))
            ] if add_notify_users_ids else False)
        return res

    @api.model_create_multi
    def create(self, vals):
        """Super create function to check weather approval_type field
        is enabled if so add the res.users to approval_type user groups"""
        if vals[0].get('approval_type'):
            self.env.ref(
                'all_in_one_dynamic_approvals_pro.approval_type').user_ids = [
                fields.Command.link(id) for id in
                self.env['res.users'].search([]).mapped('id')]
        else:
            self.env.ref(
                'all_in_one_dynamic_approvals_pro.approval_type').user_ids = [
                fields.Command.clear()]
        res = super().create(vals)
        return res

    @api.onchange('is_notify_approval_cancel', 'is_notify_approval_add')
    def _onchange_is_notify_approval_cancel(self):
        """Function to clear the values in the notify_users_ids
        if is_notify_approval_cancel is set to false"""
        if not self.is_notify_approval_cancel:
            self.cancel_notify_users_ids = [fields.Command.clear()]
        if not self.is_notify_approval_add:
            self.add_notify_users_ids = [fields.Command.clear()]

