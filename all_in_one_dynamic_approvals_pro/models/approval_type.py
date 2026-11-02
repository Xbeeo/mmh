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
# #######################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalType(models.Model):
    _name = 'approval.type'
    _description = 'Create approval type for dynamic approval creation'
    _rec_name = 'name'

    name = fields.Char(string='Name', help='Name for the record', required=True)
    approval_type = fields.Selection(selection=[('normal', 'Normal Approval'),
                                                ('manager',
                                                 'Employee Manager Approval'),
                                                ('custom', 'Custom Approval')],
                                     string="Approval Type", required=True,
                                     help='Select the approval type')
    model_id = fields.Many2one('ir.model', string='Model',
                               help='Choose a model to set the approval type')
    fields_id = fields.Many2one('ir.model.fields',
                                domain="[('model_id', '=', model_id), "
                                       "('relation', 'in',['res.users', "
                                       "'hr.employee'])]")
    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('confirm', 'Confirm')
    ], default='draft', string='State', help='Determines the records current '
                                             'state')

    def check_approval_type(self):
        """Function triggered when confirm button is clicked"""
        self.state = 'confirm'
        if self.approval_type != 'normal':
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': _('This features only works if corresponding '
                                 'user satisfies the approval type'),
                    'type': 'rainbow_man',
                }
            }

    @api.model_create_multi
    def create(self, vals_list):
        """Super create function to check weather an approval
        type is already created"""
        if self.search(
                [('approval_type', '=', vals_list[0].get('approval_type')),
                 ('model_id', '=', vals_list[0].get('model_id')),
                 ('fields_id', '=', vals_list[0].get('fields_id'))]):
            raise UserError(
                _(f"""For selected model {vals_list[0].get('approval_type'
                                                           )} approval type 
                                                           is already 
                                                           created"""))
        else:
            return super().create(vals_list)
