from odoo import fields, models


class StockExpiryWizard(models.TransientModel):
    _name = 'stock.expiry.wizard'
    _description = 'Stock Expiry Report Wizard'

    date_from = fields.Date(required=True, default=fields.Date.context_today)
    date_to = fields.Date(required=True, default=fields.Date.context_today)

    def action_print(self):
        return self.env.ref('xbo_mmh_report.action_stock_expiry_xlsx').report_action(self)