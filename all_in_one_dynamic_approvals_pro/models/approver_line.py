# -*- coding: utf-8 -*-
#####################################################################################

# Keffah Solutions the Est. Information technology and Communication  Pvt. Ltd.
#
# Copyright (C) 2021-TODAY Keffah Solutions the Est. Information technology and Communication Pvt. Ltd
# (<https://www.kascco.sa>).
# Author: Keffah Solutions the Est. Information technology and Communication Pvt. Ltd (Contact : itcs@kascco.sa)
#
# This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

#######################################################################################

from odoo import api, fields, models


class ApproverLine(models.Model):
    """Created model for approver line"""
    _name = 'approver.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Approver  Line'

    handler = fields.Integer(default='1')
    sequence = fields.Integer(string='Approver Sequence', readonly=True,
                              help="Sequence order of approver to approve "
                                   "a particular request",
                              compute="_compute_sequence")
    model_id = fields.Many2one('ir.model',
                               related="approver_id.model_id",
                               string='Model',
                               help="Represents the model of approval model")
    approver_id = fields.Many2one('dynamic.approval',
                                  string="Approval id", help="Approval id of "
                                                             "this approval "
                                                             "line")
    user_ids = fields.Many2one('res.users', string='Approver',
                               tracking=True, help="Approver for the approval"
                                                   "of the record")
    time_limit_active = fields.Boolean(string="Manual LimitActive",
                                       related="approver_id.enable_time_limit",
                                       help="check the Manuall time limit is "
                                            "active or not")
    individual_time_active = fields.Boolean(string="Individual LimitActive",
                                            related="approver_id"
                                                    ".individual_time_limit",
                                            help="check the individual time "
                                                 "limit is active or not")
    approver_time_limit = fields.Float(string="Approver Time Limit",
                                       related="approver_id.timer",
                                       help="Time limit given for "
                                            "this approver to approve "
                                            "the records related",
                                       readonly=True)
    approval_type_id = fields.Many2one('approval.type',
                                       string='Approval Type',
                                       required=True,
                                       help='Choose a approval type to continue'
                                       , domain="[('model_id', '=', model_id),"
                                                "('state', '=', 'confirm')]")
    individual_time_limit = fields.Float(
        string="Approver Individual Time Limit", help="Particular time given "
                                                      "for this approver to "
                                                      "approve to approve the "
                                                      "records")
    approver_field_id = fields.Many2one('ir.model.fields',
                                        related='approval_type_id.fields_id',
                                        string='Approver Field')
    approval_type = fields.Selection(related='approval_type_id.approval_type',
                                     help='Approval type of selected '
                                          'approval_type_id')
    state_domain = fields.Many2many('ir.model.fields.selection',
                                    related='approver_id.model_states')
    model_states = fields.Many2one('ir.model.fields.selection',
                                   string='Model State',
                                   help='Specify the model state for the user',
                                   domain="[('id', 'in', state_domain)]")
    stage_domain_ids = fields.Many2many('model.data',
                                        related='approver_id.record_ids')
    model_stage_id = fields.Many2one('model.data',
                                     domain="[('id', 'in', stage_domain_ids)]")
    check_state_type = fields.Boolean(related='approver_id.check_states_type')

    @api.depends('handler', 'approver_id.approval_method', 'approver_id.users')
    def _compute_sequence(self):
        """Compute the sequence based on the selected approval_method"""
        if self.approver_id.approval_method == 'parallel':
            for rec in self:
                rec.sequence = 1
        else:
            for rec in self:
                rec.sequence = rec.handler

    @api.onchange('approval_type_id')
    def _onchange_approval_type_id(self):
        """Clears the valur in the field on change approval_type_id"""
        self.user_ids = [fields.Command.clear()]

    def unlink(self):
        """Super unlink to message post in dynamic approval's chatter
        on deletion of approves"""
        for rec in self:
            if rec.approval_type == 'manager':
                body = f'''{rec.env.user.name} removed {rec.approval_type} approval (Approval sequence {rec.sequence})'''
            elif rec.approval_type == 'custom':
                body = f'''{rec.env.user.name} removed {rec.approval_type} approval (Approval sequence {rec.sequence}) '''
            else:
                body = f'''{rec.env.user.name} removed {rec.user_ids.name} (Approver {rec.sequence})'''
            rec.approver_id.message_post(body=body)
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """Super create function to post message in dynamic approval's
        chatter on creations on approves"""
        for rec in vals_list:
            approval_type = self.env['approval.type'].browse(
                rec.get('approval_type_id')).approval_type
            if approval_type == 'manager':
                body = f'''{self.env.user.name} added {approval_type} approval (Approval sequence {rec.get('handler')}) '''
            elif approval_type == 'custom':
                body = f'''{self.env.user.name} added {approval_type} approval (Approval sequence {rec.get('handler')}) '''
            else:
                body = f'''{self.env.user.name} added {self.env['res.users'].browse(rec.get('user_ids')).name} as (Approver {rec.get('handler')}) '''
            self.env['dynamic.approval'].browse(
                rec.get('approver_id')).message_post(
                body=body)
        return super().create(vals_list)
