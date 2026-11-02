from datetime import datetime, time

from odoo import models


class StockExpiryXlsx(models.AbstractModel):
    _name = 'report.xbo_mmh_report.stock_expiry_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Stock Expiry XLSX'

    def generate_xlsx_report(self, workbook, data, objs):
        wiz = objs[0]
        sheet = workbook.add_worksheet('Stock Expiry')
        title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center_across'})
        sub = workbook.add_format({'bold': True, 'align': 'center_across'})
        bold = workbook.add_format({'bold': True, 'border': 1})
        num = workbook.add_format({'num_format': '#,##0.00'})
        dte = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'left'})
        for c in range(6):
            sheet.write(0, c, 'Stock Expiry Report' if c == 0 else '', title)
            sheet.write(1, c, 'From %s To %s' % (wiz.date_from.strftime('%d-%b-%Y'),
                                                  wiz.date_to.strftime('%d-%b-%Y')) if c == 0 else '', sub)
        for col, h in enumerate(['Item', 'Lot', 'On Hand Qty', 'Expiration Date', 'Unit Cost', 'Amount']):
            sheet.write(3, col, h, bold)
        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 5, 18)
        lots = self.env['stock.lot'].search([
            ('expiration_date', '>=', datetime.combine(wiz.date_from, time.min)),
            ('expiration_date', '<=', datetime.combine(wiz.date_to, time.max)),
        ], order='expiration_date')
        row = 4
        for l in lots:
            cost = l.standard_price or l.product_id.standard_price
            sheet.write(row, 0, l.product_id.display_name)
            sheet.write(row, 1, l.name)
            sheet.write(row, 2, l.product_qty, num)
            sheet.write_datetime(row, 3, l.expiration_date, dte)
            sheet.write(row, 4, cost, num)
            sheet.write(row, 5, l.product_qty * cost, num)
            row += 1