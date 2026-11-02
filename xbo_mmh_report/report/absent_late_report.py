from odoo import models


class AbsentLateEmployeeReport(models.AbstractModel):
    _name = 'report.xbo_mmh_report.report_absent_late_employee'
    _description = 'Absent & Late Employee PDF Report'

    def _get_report_values(self, docids, data=None):

        wizard = self.env['absent.late.wizard'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'absent.late.wizard',
            'docs': wizard,
            'lines': wizard._get_report_lines(),
        }