# -*- coding: utf-8 -*-

import itertools
import logging
from collections import defaultdict
from odoo import _, api, fields, models, tools
from .view_access import hide_edit_buttons, PRODUCT_EDITOR_GROUP
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.image import is_image_size_above

_logger = logging.getLogger(__name__)
PRICE_CONTEXT_KEYS = ['pricelist', 'quantity', 'uom', 'date']




class ProductTemplateInheritFRM(models.Model):
    _inherit = 'product.template'

    is_checkup_fees = fields.Boolean(string="Is Checkup Fees", tracking=True)
    is_doctor_share = fields.Boolean(string="Is Doctor Share", tracking=True)

    name = fields.Char('Name', index='trigram', required=True, translate=True, tracking=True)
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_user",
        help="""Value of the product (automatically computed in AVCO).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""", tracking=True)


    type = fields.Selection(
        string="Product Type",
        help="Goods are tangible materials and merchandise you provide.\n"
             "A service is a non-material product you provide.",
        selection=[
            ('consu', "Goods"),
            ('service', "Service"),
            ('combo', "Combo"),
        ],
        required=True,
        default='consu',
        tracking=True)
    margin_percentage = fields.Float(
        string='Margin %',default=5.0,
    )

    @api.onchange('margin_percentage','standard_price')
    def _onchange_margin_percentage(self):
        for rec in self:
            if rec.standard_price and rec.margin_percentage:
                margin_amount = rec.standard_price * (rec.margin_percentage / 100)
                rec.list_price = rec.standard_price + margin_amount

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('product.product_category_goods')

    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True, tracking=True)


    @tools.ormcache()
    def _get_default_uom_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('uom.product_uom_unit')

    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for all stock operations.", tracking=True)

    barcode = fields.Char('Barcode', compute='_compute_barcode', inverse='_set_barcode', search='_search_barcode', tracking=True)
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True, tracking=True)

    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the product without removing it.", tracking=True)

    use_expiration_date = fields.Boolean(string='Use Expiration Date',
                                         help='When this box is ticked, you have the possibility to specify dates to manage'
                                              ' product expiration, on the product and on the corresponding lot/serial numbers', tracking=True)

    create_mrp_order = fields.Boolean(string="To Create MRP Order")
    done_mrp_order = fields.Boolean(string="Done MRP Order")

    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account')


    @api.model
    def _get_buy_route(self):
        buy_route = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)
        if buy_route:
            return self.env['stock.route'].search([('id', '=', buy_route.id)]).ids
        return []

    route_ids = fields.Many2many(default=lambda self: self._get_buy_route(), tracking=True)

    sale_ok = fields.Boolean('Sales', default=True, tracking=True)
    purchase_ok = fields.Boolean('Purchase', default=True, compute='_compute_purchase_ok', store=True, readonly=False, tracking=True)
    available_in_pos = fields.Boolean(string='Available in POS',
                                      help='Check if you want this product to appear in the Point of Sale.',
                                      default=False, tracking=True)

    def action_update_medicament(self):
        product_obj = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        obj = self.env['medical.medicament'].search([('product_id','in',product_obj.ids)])
        if obj:
            for x in obj:
                x.price  = self.list_price
                x.qty_available = self.qty_available

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = dict(super().get_view(view_id, view_type, **options))
        return hide_edit_buttons(self.env, result, PRODUCT_EDITOR_GROUP)