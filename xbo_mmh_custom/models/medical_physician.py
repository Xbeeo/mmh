from odoo import models, fields, api


class MedicalPhysician(models.Model):
    _inherit = 'medical.physician'

    cnic = fields.Char(string='CNIC')
    phone = fields.Char(string='Phone No')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.cnic = self.partner_id.patient_cnic
        self.phone = self.partner_id.phone