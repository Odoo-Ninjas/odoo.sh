# Copyright 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def update_bank_journals(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ajo = env["account.journal"]
    journals = ajo.search([("type", "=", "bank")])
    sdd = env.ref("account_banking_sepa_direct_debit.sepa_direct_debit")
    if sdd:
        journals.write(
            {
                "inbound_payment_method_line_ids": [
                    (
                        0,
                        0,
                        {"payment_method_id": sdd.id, "name": "SEPA Direct Debit"},
                    )
                ]
            }
        )
    return
