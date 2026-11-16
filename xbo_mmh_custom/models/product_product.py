# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from .view_access import hide_edit_buttons, PRODUCT_EDITOR_GROUP

class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    is_checkup_fees = fields.Boolean(string="Is Checkup Fees", related='product_tmpl_id.is_checkup_fees', store=True)
    is_doctor_share = fields.Boolean(string="Is Doctor Share", related='product_tmpl_id.is_doctor_share', store=True)

    create_mrp_order = fields.Boolean(string="To Create MRP Order",related='product_tmpl_id.create_mrp_order', store=True)
    done_mrp_order = fields.Boolean(string="Done MRP Order",related='product_tmpl_id.done_mrp_order', store=True)

    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account',related='product_tmpl_id.analytic_account_id', store=True)

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = dict(super().get_view(view_id, view_type, **options))
        return hide_edit_buttons(self.env, result, PRODUCT_EDITOR_GROUP)