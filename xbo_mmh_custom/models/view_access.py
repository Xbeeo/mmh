from lxml import etree
import ast
PRODUCT_EDITOR_GROUP = 'xbo_mmh_custom.group_product_editor'
ACCOUNT_EDITOR_GROUP = 'xbo_mmh_custom.group_account_editor'


CREATE_RULES = {
    'product.product': PRODUCT_EDITOR_GROUP,
    'product.template': PRODUCT_EDITOR_GROUP,
    'account.account': ACCOUNT_EDITOR_GROUP,
}



def hide_edit_buttons(env, result, group):
    if env.su or env.user.has_group(group):
        return result

    node = etree.fromstring(result['arch'])
    node.set('create', '0')
    node.set('edit', '0')
    node.set('delete', '0')
    node.set('import', '0')
    result['arch'] = etree.tostring(node, encoding='unicode')
    return result

def _block_create_option(field_node):
    raw = field_node.get('options')
    try:
        options = ast.literal_eval(raw) if raw else {}
    except Exception:
        options = {}
    options['no_create'] = True
    options['no_quick_create'] = True
    options['no_create_edit'] = True
    field_node.set('options', str(options))


def hide_relation_create(env, node, model_name):
    fields = env[model_name]._fields
    for child in node:
        if child.tag != 'field':
            hide_relation_create(env, child, model_name)
            continue
        field = fields.get(child.get('name'))
        if not field or not field.relational:
            continue
        group = CREATE_RULES.get(field.comodel_name)
        if group and not env.user.has_group(group):
            _block_create_option(child)
        for sub in child:
            if sub.tag in ('list', 'form', 'kanban'):
                hide_relation_create(env, sub, field.comodel_name)