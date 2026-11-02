from odoo import models


class InventoryAnalysisXlsx(models.AbstractModel):
    _name = 'report.xbo_mmh_report.inv_analysis_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Inventory Analysis Summary XLSX'

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet('Inventory Analysis')
        title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        bold = workbook.add_format({'bold': True, 'border': 1})
        num = workbook.add_format({'num_format': '#,##0.00'})
        sheet.merge_range(0, 0, 0, 3, 'Inventory Analysis Report', title)
        for col, h in enumerate(['Product', 'On Hand Qty', 'Unit Cost Price', 'Amount']):
            sheet.write(2, col, h, bold)
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 3, 18)
        products = self.env['product.product'].search([('active', '=', True)])
        row = 3
        for p in products:
            sheet.write(row, 0, p.display_name)
            sheet.write(row, 1, p.qty_available, num)
            sheet.write(row, 2, p.standard_price, num)
            sheet.write(row, 3, p.qty_available * p.standard_price, num)
            row += 1