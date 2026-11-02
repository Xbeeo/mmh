from datetime import datetime, time

from odoo import models


class PurchaseAnalysisXlsx(models.AbstractModel):
    _name = 'report.xbo_mmh_report.purchase_analysis_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Purchase Analysis XLSX'

    def generate_xlsx_report(self, workbook, data, objs):
        w = objs[0]
        dom = [
            ('state', '!=', 'cancel'),
            ('date_order', '>=', datetime.combine(w.date_from, time.min)),
            ('date_order', '<=', datetime.combine(w.date_to, time.max)),
        ]
        if w.partner_id:
            dom.append(('partner_id', '=', w.partner_id.id))
        if w.product_id:
            dom.append(('order_line.product_id', '=', w.product_id.id))
        if w.open_purchase:
            dom.append(('receipt_status', 'in', ['pending', 'partial']))
        orders = self.env['purchase.order'].search(dom, order='date_order')

        show_vendor = bool(w.partner_id or w.open_purchase or w.pending_payment)
        show_qty = bool(w.product_id or w.partner_id)

        # (header, getter(order, line, due), kind)
        cols = [('Date', lambda o, l, d: o.date_order.date(), 'd'),
                ('PO Number', lambda o, l, d: o.name, 't')]
        if show_vendor:
            cols.append(('Vendor', lambda o, l, d: o.partner_id.name, 't'))
        cols.append(('Item', lambda o, l, d: l.product_id.display_name or l.name, 't'))
        if show_qty:
            cols += [('Quantity', lambda o, l, d: l.product_qty, 'n'),
                     ('Rate', lambda o, l, d: l.price_unit, 'n')]
        if w.open_purchase:
            cols.append(('Delivery Date', lambda o, l, d: l.date_planned and l.date_planned.date(), 'd'))
        if w.pending_payment:
            cols.append(('Bill Due Date', lambda o, l, d: d, 'd'))
        cols.append(('Amount', lambda o, l, d: l.price_total, 'n'))

        sheet = workbook.add_worksheet('Purchase Analysis')
        title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center_across'})
        sub = workbook.add_format({'bold': True, 'align': 'center_across'})
        bold = workbook.add_format({'bold': True, 'border': 1})
        num = workbook.add_format({'num_format': '#,##0.00'})
        dte = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'left'})
        rng = 'From %s To %s' % (w.date_from.strftime('%d-%b-%Y'), w.date_to.strftime('%d-%b-%Y'))
        for c in range(len(cols)):
            sheet.write(0, c, 'Purchase Analysis Report' if c == 0 else '', title)
            sheet.write(1, c, rng if c == 0 else '', sub)
        for c, col in enumerate(cols):
            sheet.write(3, c, col[0], bold)
        sheet.set_column(0, len(cols) - 1, 18)
        sheet.set_column(2, 3, 30)

        row = 4
        for o in orders:
            due = False
            if w.pending_payment:
                inv = o.invoice_ids.filtered(
                    lambda i: i.state == 'posted' and i.payment_state in ('not_paid', 'partial'))
                if not inv:
                    continue
                dues = [d for d in inv.mapped('invoice_date_due') if d]
                due = min(dues) if dues else False
            lines = o.order_line.filtered(
                lambda l: not l.display_type and (not w.product_id or l.product_id == w.product_id))
            for l in lines:
                for c, (h, fn, kind) in enumerate(cols):
                    v = fn(o, l, due)
                    if kind == 'd':
                        sheet.write_datetime(row, c, v, dte) if v else sheet.write_blank(row, c, None)
                    elif kind == 'n':
                        sheet.write(row, c, v, num)
                    else:
                        sheet.write(row, c, v)
                row += 1