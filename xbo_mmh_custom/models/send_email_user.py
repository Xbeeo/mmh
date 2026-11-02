import base64
import pytz

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SendEmailUser(models.Model):
    _name = 'send.email.user'
    _description = 'Send Email User'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True
    )

    email = fields.Char(
        string='Email',
        required=True,
        tracking=True
    )

    @api.model
    def send_daily_absent_late_report(self):

        # Current date according to Pakistan timezone
        tz = pytz.timezone('Asia/Karachi')
        today = fields.Date.context_today(
            self.with_context(tz='Asia/Karachi')
        )

        # Get all configured email users
        email_users = self.sudo().search([
            ('email', '!=', False)
        ])

        if not email_users:
            return

        # Create report wizard
        wizard = self.env['absent.late.wizard'].sudo().create({
            'date_from': today,
            'date_to': today,
        })

        # Generate PDF
        report = self.env.ref(
            'xbo_mmh_report.action_absent_late_employee_report'
        )

        pdf_content, content_type = self.env[
            'ir.actions.report'
        ].sudo()._render_qweb_pdf(
            report.report_name,
            res_ids=wizard.ids
        )

        # Create PDF attachment
        attachment = self.env['ir.attachment'].sudo().create({
            'name': f'Absent_Late_Employee_{today}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'mimetype': 'application/pdf',
        })

        # Send email to every configured user
        for user in email_users:

            mail_values = {
                'subject': f'Absent & Late Employee Report - {today}',
                'body_html': f"""
                    <div>
                        <p>Dear {user.name},</p>

                        <p>
                            Please find attached the daily
                            Absent & Late Employee Report.
                        </p>

                        <p>
                            <b>Report Date:</b> {today}
                        </p>

                        <p>Regards,<br/>HR Department</p>
                    </div>
                """,
                'email_to': user.email,
                'attachment_ids': [(4, attachment.id)],
            }

            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()

        # Delete temporary wizard
        wizard.sudo().unlink()