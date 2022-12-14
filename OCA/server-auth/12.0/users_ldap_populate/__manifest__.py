# Copyright 2012-2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).
{
    "name": "LDAP Populate",
    "version": "12.0.1.0.2",
    "author": "Therp BV, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/server-auth',
    "license": "AGPL-3",
    "category": 'Tools',
    "depends": [
        'auth_ldap',
    ],
    'external_dependencies': {
        'python': ['ldap'],
    },
    "data": [
        'views/users_ldap.xml',
        'views/populate_wizard.xml',
    ],
    'installable': True,
}
