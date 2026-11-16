from lxml import etree
from odoo import models, api
from .view_access import hide_relation_create


class BaseViewAccess(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = dict(super().get_view(view_id, view_type, **options))
        if self.env.su or view_type not in ('form', 'list', 'kanban'):
            return result
        node = etree.fromstring(result['arch'])
        hide_relation_create(self.env, node, self._name)
        result['arch'] = etree.tostring(node, encoding='unicode')
        return result