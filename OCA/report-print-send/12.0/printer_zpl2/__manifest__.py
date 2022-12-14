# Copyright (C) 2016 SUBTENO-IT (<https://subteno-it.fr>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Printer ZPL II',
    'version': '12.0.1.1.0',
    'category': 'Printer',
    'author': 'SUBTENO-IT, FLorent de Labarre, '
              'Apertoso NV, Odoo Community Association (OCA)',
    'website': 'http://www.syleam.fr/',
    'license': 'AGPL-3',
    'external_dependencies': {
        'python': ['zpl2'],
    },
    'depends': [
        'base_report_to_printer',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/printing_label_zpl2.xml',
        'wizard/print_record_label.xml',
        'wizard/wizard_import_zpl2.xml',
    ],
    'installable': True,
}
