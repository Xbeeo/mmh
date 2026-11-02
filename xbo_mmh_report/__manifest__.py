# -*- coding: utf-8 -*-
{
    "name": "Xbo MMH Report",

    'version': '19.0.0.0',

    'summary': """Xbo MMH Report""",

    'description': """Xbo MMH Report""",

    'category': 'MMH',

    'author': "xbeeo",

    'website': 'https://xbeeo.com',

    "depends": ['base', 'xbo_mmh_custom', 'basic_hms','hr_expense'],

    "data": [
        'security/ir.model.access.csv',
        'report/multidays_profit_loss_template.xml',
        'report/pos_profit_loss_report_template.xml',
        'report/report_partner_ledger.xml',
        'report/current_balance_report_template.xml',
        'report/patient_discharge_slip_report.xml',
        'report/lab_test_report_template.xml',
        'report/patient_card_report_template.xml',
        'report/sale_summary_report_template.xml',
        'report/medical_inpatient_registration.xml',
        'report/hospital_discharge_slip.xml',
        'report/report_purchase_order_inherit.xml',
        'report/bulk_expense_report.xml',
        'report/income_report_template.xml',
        'report/inventory_analysis_report.xml',
        'report/absent_late_report.xml',
        'report/stock_expiry_report.xml',
        'report/purchase_analysis_report.xml',
        'report/report_action.xml',
        'wizards/multidays_profit_loss_wizard.xml',
        'wizards/pos_profit_loss_wizard_views.xml',
        'wizards/customer_balance_wizard_views.xml',
        'wizards/vendor_balance_views.xml',
        'wizards/discharge_slip_wizard_views.xml',
        'wizards/absent_late_wizard_views.xml',
        'wizards/sales_summary_report_wizard_view.xml',
        'wizards/bulk_expense_wizard_views.xml',
        'wizards/sale_analysis_wizard_views.xml',
        'wizards/patient_analysis_wizard_views.xml',
        'wizards/stock_expiry_wizard_views.xml',
        'wizards/purchase_analysis_wizard_views.xml',
        'wizards/income_report_wizard_views.xml',

    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,

}
