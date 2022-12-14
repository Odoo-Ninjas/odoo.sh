# Copyright (C) 2013-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Authentification - System Administrator Passkey',
    'summary': "Allows system administrator to authenticate with any account",
    'version': '12.0.1.1.1',
    'category': 'base',
    'author': "GRAP,Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/server-auth',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'views/res_users_views.xml',
    ],
    'installable': True,
}
