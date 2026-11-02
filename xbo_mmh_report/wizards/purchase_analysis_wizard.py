from odoo import fields, models
from odoo.exceptions import UserError


class PurchaseAnalysisWizard(models.TransientModel):
    _name = 'purchase.analysis.wizard'
    _description = 'Purchase Analysis Wizard'

    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    product_id = fields.Many2one('product.product', string='Item')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    open_purchase = fields.Boolean()
    pending_payment = fields.Boolean(string='Pending Payments')

    def action_print(self):
        if not (self.product_id or self.partner_id or self.open_purchase or self.pending_payment):
            raise UserError('Please select at least one filter: Item, Vendor, Open Purchase or Pending Payments.')
        if self.date_from > self.date_to:
            raise UserError('Date From cannot be after Date To.')
        return self.env.ref('xbo_mmh_report.action_purchase_analysis_xlsx').report_action(self)