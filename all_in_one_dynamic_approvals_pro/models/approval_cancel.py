# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo import models, fields, api


class ApprovalCancel(models.Model):
    _name = 'approval.cancel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Approval Cancel'
    _rec_name = 'name'

    name = fields.Char(default="Approval cancelled for ", help='Name for the '
                                                               'records in '
                                                               'this model',
                       string='Name')
    model_id = fields.Many2one('ir.model', string='Model',
                               domain="[('is_approval', '=', True)]",
                               help='Choose a model to cancel approval for '
                                    'its records'
                               )
    record_ids = fields.Many2many('model.data', string="Records",
                                  domain="[('save', '!=', True)]",
                                  help='Choose records to cancel the approval')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed')],
                             default='draft', help='Represents the state of '
                                                   'the current record')

    @api.onchange('model_id')
    def _show_records(self):
        """The function shows the records of model with active approvals in
        it"""
        records = self.env['model.data'].search([('save', '!=', True)])
        if records:
            for rec in records:
                rec.unlink()
        if self.model_id:
            values = self.env[self.model_id.model].search([('x_approval_id',
                                                            '!=', False)])
            for vals in values:
                self.env['model.data'].create({
                    'rec_name': vals.name,
                    'rec_id': str(vals.id)
                })

    def cancel_approval(self):
        """This function cancel the approval if one is set to it."""
        for rec in self:
            model = rec.model_id
            records = rec.record_ids.mapped('rec_id')
            value_list = [int(val) for val in records]
            records = self.env[model.model].search(
                [('id', 'in', value_list)])
            for recs in records:
                recs.write({
                    'x_approval_id': False,
                    'x_need_to_approve': False
                })
        for record in self.record_ids:
            record.approval_type = 'cancel'
            record.save = True
            self.name = self.name + record.rec_name + ", "
        self.state = 'confirm'
