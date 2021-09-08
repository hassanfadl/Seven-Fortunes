# -*- coding: utf-8 -*-
{
    'name': "Employment Contract",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "PerfectTeck/hatem",
    'website': "https://www.linkedin.com/in/hatem-mostafa-a6267b1a9",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_contract'],

    # always loaded
    'data': [
        'report/report.xml',
        'views/hr_contract.xml'
    ],
}
