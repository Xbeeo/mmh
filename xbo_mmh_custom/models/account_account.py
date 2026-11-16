from odoo import models, api
from .view_access import hide_edit_buttons, ACCOUNT_EDITOR_GROUP


class AccountAccountAccess(models.Model):
    _inherit = 'account.account'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = dict(super().get_view(view_id, view_type, **options))
        return hide_edit_buttons(self.env, result, ACCOUNT_EDITOR_GROUP)