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

from odoo import models


class CrmLead(models.Model):
    """Inherited CrmLead to change the functionality"""
    _inherit = 'crm.lead'

    def action_new_quotation(self):
        """Super action_new_quotation to add context value if
        dynamic approval set to sale.order"""
        super_vals = super().action_new_quotation()
        approval = self.env['dynamic.approval'].search([
            ('model_id.model', '=', 'sale.order'),
            ('state', 'in', ['active', 'multi_state_activated', 'old'])])
        if approval:
            super_vals['context']['default_x_approval_id'] = 1
            super_vals['context']['default_x_approve_state'] = 'approve'
            super_vals['context']['default_x_multi_state'] = True
            super_vals['context']['defauaction_new_quotationlt_x_need_to_approve'] = False
            super_vals['context']['default_company_id'] = self.env.company.id
        return super_vals
