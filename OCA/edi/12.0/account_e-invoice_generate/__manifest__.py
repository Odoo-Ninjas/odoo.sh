# Copyright 2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Account e-invoice Generate',
    'version': '12.0.1.1.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Technical module to generate PDF invoices with '
               'embedded XML file',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': ['account'],
    'data': [
        'views/res_config_settings.xml',
    ],
    'installable': True,
}
