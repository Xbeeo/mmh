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
from odoo import models, fields, api


class AddApproval(models.Model):
    _name = 'add.approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Add Approval'
    _rec_name = 'name'

    model_id = fields.Many2one('ir.model', required=True,
                               domain="[('is_approval', '=', True)]",
                               ondelete='cascade',
                               string="Model", help="Select a model")
    name = fields.Char(default='Added approval for ', help='Name for the '
                                                           'records in the '
                                                           'model',
                       string='Name')
    record_ids = fields.Many2many('model.data', string='Records',
                                  help='Choose records to add approval for it',
                                  domain="[('save', '!=', True)]"
                                  )
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed')], string='state',
                             help='State representation of current record',
                             default='draft')

    @api.onchange('model_id')
    def _show_records(self):
        """This function shows the records in the current selected model to
        add approval"""
        records = self.env['model.data'].search([('save', '!=', True)])
        if records:
            for rec in records:
                rec.unlink()
        if self.model_id:
            values = self.env[self.model_id.model].search([('x_approval_id',
                                                            '=', False)])
            for vals in values:
                self.env['model.data'].create({
                    'rec_name': vals.name,
                    'rec_id': str(vals.id)
                })

    def add_approve(self):
        """This function adds approval to the selected records"""
        for rec in self:
            model = rec.model_id
            records = rec.record_ids.mapped('rec_id')
            approval = self.env['dynamic.approval'].search([
                ('state', 'not in', ['draft', 'cancel']),
                ('model_id', '=', model.id)])
            value_list = [int(val) for val in records]
            records = self.env[model.model].search(
                [('id', 'in', value_list)])
            for recs in records:
                if recs.x_compute_one:
                    recs.sudo().write({
                        'x_approval_id': approval.id,
                        'x_compute_one': False,
                    })
                else:
                    recs.sudo().write({
                        'x_approval_id': approval.id,
                        'x_compute_one': True,
                    })
        for record in self.record_ids:
            record.approval_type = 'add'
            record.save = True
            self.name = self.name + record.rec_name + ", "
        self.state = 'confirm'
