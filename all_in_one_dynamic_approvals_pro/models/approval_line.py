# -*- coding: utf-8 -*-
#####################################################################################
#
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

from odoo import models, fields


class ApprovalLine(models.Model):
    _name = 'approval.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Approval Order Line'

    sequence = fields.Integer(string='Approver Sequence', help='Sequence of '
                                                               'approver')
    approval_id = fields.Many2one('dynamic.approval')
    approver_id = fields.Many2one('res.users', string='Approver',
                                  help='Approver of the created approval')
    approval_type_id = fields.Many2one('approval.type',
                                       string='Approval Type',
                                       help='Choose a approval type to continue'
                                       , domain="[('model_id', '=', model_id),"
                                                "('state', '=', 'confirm')]")
    reject_reason = fields.Text(string='Reject Reason', help='Cause of reject '
                                                             'reason')
    time_limit = fields.Integer(string="Approver Time Limit",
                                help="Time limit of approver")
    delay = fields.Boolean(string="Approval Delayed",
                           help="The approver given time limit is crossed. "
                                "The approval is esculated to the authority")
    authority_email_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Email Sent')],
        string="Authority Email Status", readonly=False, default='draft',
        tracking=True, help='Email status of authority')
    is_send = fields.Boolean(string="Is send",
                             help="Check the approval requested person delay "
                                  "info mail sent or not")
    start_date = fields.Datetime(string='Start Date', help='Start date')
    end_date = fields.Datetime(string='End Date', help='End date')
    approval_duration = fields.Char(string='Approval Duration',
                                    help='Approval Duration')
    approval_email_status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Email Sent')],
        string="Email Status", readonly=False, default='draft', tracking=True)
    approval_status = fields.Selection([
        ('approve', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('reject', 'Reject')],
        help='Approval status',
        string="Status", readonly=False, default='draft', tracking=True)
    approve_state = fields.Many2one('ir.model.fields.selection',
                                    string='Approval state',
                                    help='Approver of the line Approves '
                                         'record in this state')
    approve_stage_id = fields.Many2one('model.data',
                                       string='Approve state')
