# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Edi Account",
    "summary": """
        Define EDI Configuration for Account Moves""",
    "version": "13.0.2.0.1",
    "license": "LGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account", "edi", "component_event"],
    "data": [
        "views/account_journal.xml",
        "views/res_partner.xml",
        "views/account_move.xml",
        "views/edi_exchange_record.xml",
    ],
    "demo": [],
}
