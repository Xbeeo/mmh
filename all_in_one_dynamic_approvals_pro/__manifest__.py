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
########################################################################################
{
    'name': 'All in One Dynamic Approvals Pro',
    'version': '19.0.0.0',
    'category': 'All',
    'summary': 'Create dynamic approval to any model.',
    'description': 'you can create desirable approvals without any '
                   'customizations. The app can create approval dynamically. It '
                   'supports all modules contains the Header, State fields with '
                   'Selection Type, Company field and Context. The application '
                   'can be support in Odoo Community and Enterprise versions. The '
                   'new features will be freely available on the app update. The '
                   'approval does not affect old records, Instead it will be '
                   'applicable only for newly created records.',
    'author': 'Keffah Solutions the Est. Information Technology and '
              'Communication',
    'company': 'Keffah Solutions the Est. Information Technology and '
               'Communication',
    'maintainer': 'Keffah Solutions the Est. Information Technology and '
                  'Communication',
    'website': 'https://www.kascco.sa',
    'depends': ['base', 'base_automation', 'hr', 'sale_crm'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/approval_sequence.xml',
        'views/approval.xml',
        'views/approval_cancel.xml',
        'views/approval_add.xml',
        'wizard/approval_reject_reason.xml',
        'views/res_config_settings_views.xml',
        'views/approval_type.xml',
        'report/all_in_one_dynamic_approvals_pro_templates.xml',
        'report/all_in_one_dynamic_approvals_pro_reports.xml',
        'data/mail_template_data.xml',
    ],
    'images': ['static/description/banner_.png'],
    'license': 'OPL-1',
    'price': 299.00,
    'currency': 'USD',
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': '_post_init_set_is_notify_approval_cancel',
}
