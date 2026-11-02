# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
######################################################################################
#
#    Keffah Solutions the Est. Information technology and Communication  Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Keffah Solutions the Est. Information technology and Communication Pvt. Ltd
#    (<https://www.kascco.sa>).
#    Author: Keffah Solutions the Est. Information technology and Communication Pvt. Ltd (Contact : itcs@kascco.sa)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
# #######################################################################################


from odoo import models, fields


class ApprovalRejectReason(models.TransientModel):
    """Model for reject reasons in created approval"""
    _name = 'reject.reason'

    reject_reason = fields.Text(string='Approval Reject Reason', required=True,
                                help="Reject reason for the approval")

    def reject(self):
        """Function called when clicked the reject button from the form view"""
        origin = self._context.get('origin')
        origin_model = origin.split('(')[0]
        origin_id = int(origin.split('(')[1].split(',')[0])
        origin_obj = self.env[origin_model].browse(origin_id)
        model_id = self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_dynamic_approvals_pro.model_id')
        for user in origin_obj.x_approver_ids.filtered(
                lambda l: l.approver_id == self.env.user):
            user.write({'approval_status': 'reject',
                        'reject_reason': self.reject_reason})
            if 'reject' in origin_obj.x_approver_ids.mapped('approval_status'):
                origin_obj.write({'x_approve_state': 'reject',
                                  'x_approve': True})
                user_id = self.env.user
                subject = origin_obj._description + ' Rejected'
                mail_url = str(
                    self.env["ir.config_parameter"].sudo().get_param(
                        "web.base.url")) + '/web#' + 'id=' + str(
                    origin_obj.id) + '&model=' + str(
                    origin_obj._name) + '&view_type=form'
                self.env['mail.mail'].sudo().create({
                    'subject': subject,
                    'author_id': str(user_id.partner_id.id),
                    'email_from': str(user.approver_id.login),
                    'email_to': str(origin_obj.create_uid.login),
                    'body_html':
                        '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">'
                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
                        '<tbody>'
                        '<!-- HEADER -->'
                        '<tr>'
                        '<td align="center" style="min-width: 590px;">'
                        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                        '<tr>'
                        '<td valign="middle">'
                        '<span style="font-size: 10px;">' 'Approval Request Rejected''</span>''<br/>' +
                        '<span style="font-size: 20px; font-weight: bold;">' + origin_obj.name + '</span>'
                                                                                                 '</td>'
                                                                                                 '<td valign="middle" align="right">'
                                                                                                 '<img src="/logo.png?company= +record.company_id.logo+" style="padding: 0px; margin: 0px; height: auto; width: 80px;"/>'
                                                                                                 '</td>'
                                                                                                 '</tr>'
                                                                                                 '<tr>''<td colspan="2" style="text-align:center;">'
                                                                                                 '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                                                                 '</td>''</tr>'
                                                                                                 '</table>'
                                                                                                 '</td>'
                                                                                                 '</tr>'
                                                                                                 '<!-- CONTENT -->'
                                                                                                 '<tr>'
                                                                                                 '<td align="center" style="min-width: 590px;">'
                                                                                                 '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                                                                 '<tr>'
                                                                                                 '<td valign="top" style="font-size: 13px;">'
                                                                                                 '<div>'
                                                                                                 'Dear' + ' ' + origin_obj.create_uid.name + ',' '<br/>''<br/>'
                                                                                                                                             'Your  approval  request ' + origin_obj.name + ' ' + 'is rejected by ' + user.approver_id.name + '.'
                                                                                                                                                                                                                                              '<br/>''<br/>'
                                                                                                                                                                                                                                              '<div style="margin: 16px 0px 16px 0px;">'
                                                                                                                                                                                                                                              '<p>''Reject Reason is ' + user.reject_reason + '.' '</p>'
                                                                                                                                                                                                                                                                                              '<br/>''<br/>'
                                                                                                                                                                                                                                                                                              '<span>'
                                                                                                                                                                                                                                                                                              '<a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href=' + mail_url + '>View Record</a>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</span>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</div>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<br/>''<br/>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             'Best regards''<br/>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</div>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</td>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</tr>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<tr>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<td style="text-align:center;">'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</td>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</tr>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</table>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</td>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '</tr>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<!-- FOOTER -->'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<tr>'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<td align="center" style="min-width: 590px;">'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">'
                                                                                                                                                                                                                                                                                                                                                                                                                                                             '<tr>''<td valign="middle" align="left">'
                        + user_id.company_id.name +
                        '</td>''</tr>'
                        '<tr>''<td valign="middle" align="left" style="opacity: 0.7;">'
                        + user_id.company_id.phone +
                        '%' 'if' + user_id.company_id.email +
                        '|' '<a href="mailto:%s % +user_id.company_id.email+" style="text-decoration:none; color: #454748;">' + user_id.company_id.email + '</a>'
                                                                                                                                                           '%' 'endif'
                                                                                                                                                           '%' 'if' + user_id.company_id.website +
                        '|' '<a href="%s % +user_id.company_id.website+" style="text-decoration:none; color: #454748;">'
                        + user_id.company_id.website +
                        '</a>'
                        '%' 'endif'
                        '</td>''</tr>'
                        '</table>'
                        '</td>'
                        '</tr>'
                        '</tbody>'
                        '</table>'
                }).send()
                if self.env['ir.model'].search(
                        [('model', '=', origin_obj._name)]).is_mail_thread:
                    origin_obj.message_post(
                        body=origin_obj._description + " is Rejected and Reason is " + user.reject_reason + " .",
                        subject="Rejected")
                    origin_obj.message_post(
                        body="The request is Rejected and traceback sent to " + origin_obj.create_uid.name + " .",
                        subject="Rejection Mail")
