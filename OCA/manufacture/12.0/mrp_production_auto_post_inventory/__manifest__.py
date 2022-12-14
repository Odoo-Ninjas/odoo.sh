# Copyright 2016-19 Eficent Business and IT Consulting Services S.L.
# Copyright 2019 Lorenzo Battistini - TAKOBI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Production Auto Post-Inventory',
    'version': '12.0.1.1.1',
    'category': 'MRP',
    'author': 'Eficent, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/manufacture',
    'license': 'AGPL-3',
    'depends': [
        'mrp',
    ],
    'data': [
        'data/cron.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
}
