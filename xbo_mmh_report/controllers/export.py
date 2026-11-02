import json

from odoo import fields
from odoo.http import request, route
from odoo.addons.web.controllers.export import ExcelExport, ExportXlsxWriter

TITLES = {
    'product.template': 'MMH Product Report',
    'product.product': 'MMH Product Report',
    'hr.employee': 'MMH Employee Report',
    'purchase.order': 'MMH PO Report',
    'sale.order': 'MMH SO Report',
    'medical.patient': 'MMH Patient Report',
    'medical.prescription.order': 'MMH Prescription Report',
    'medical.inpatient.registration': 'MMH Inpatient Report',
    'medical.patient.lab.test': 'MMH Draft Lab Report',
    'medical.lab': 'MMH Lab Result Report',
}
BILL_TYPES = ('in_invoice', 'in_refund', 'in_receipt')
OFFSET = 4  # title + printed by + printed on + blank row

_write = ExportXlsxWriter.write
_write_header = ExportXlsxWriter.write_header


def write(self, row, column, value, style=None):
    if getattr(request, 'export_title', None):
        row += OFFSET
    return _write(self, row, column, value, style)


def write_header(self):
    _write_header(self)
    title = getattr(request, 'export_title', None)
    if title:
        big = self.workbook.add_format({'bold': True, 'font_size': 16})
        bold = self.workbook.add_format({'bold': True})
        now = fields.Datetime.context_timestamp(request.env.user, fields.Datetime.now())
        self.worksheet.write(0, 0, title, big)
        self.worksheet.write(1, 0, 'Printed By', bold)
        self.worksheet.write(1, 1, request.env.user.name)
        self.worksheet.write(2, 0, 'Printed On', bold)
        self.worksheet.write(2, 1, now.strftime('%d %B %Y %H:%M:%S'))


ExportXlsxWriter.write = write
ExportXlsxWriter.write_header = write_header


class ExcelExportTitle(ExcelExport):

    @route('/web/export/xlsx', type='http', auth='user', readonly=True)
    def web_export_xlsx(self, data):
        params = json.loads(data)
        model = params.get('model')
        title = TITLES.get(model)
        if model == 'account.move':
            title = self._move_title(params)
        request.export_title = title
        return super().web_export_xlsx(data)

    def _move_title(self, params):
        ids = params.get('ids')
        if ids:
            moves = request.env['account.move'].browse(ids)
        else:
            moves = request.env['account.move'].search(params.get('domain') or [], limit=1)
        if not moves:
            return 'MMH Invoice Report'
        if all(m.move_type in BILL_TYPES for m in moves):
            return 'MMH Bill Report'
        return 'MMH Invoice Report'