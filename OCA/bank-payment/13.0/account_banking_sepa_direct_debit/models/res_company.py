# Copyright 2013-2016 Akretion - Alexis de Lattre
# Copyright 2014 Tecnativa - Pedro M. Baeza
# Copyright 2016 Tecnativa - Antonio Espinosa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .common import is_sepa_creditor_identifier_valid


class ResCompany(models.Model):
    _inherit = "res.company"

    sepa_creditor_identifier = fields.Char(
        string="SEPA Creditor Identifier",
        size=35,
        help="Enter the Creditor Identifier that has been attributed to your "
        "company to make SEPA Direct Debits. This identifier is composed "
        "of :\n- your country ISO code (2 letters)\n- a 2-digits "
        "checkum\n- a 3-letters business code\n- a country-specific "
        "identifier",
    )

    @api.constrains("sepa_creditor_identifier")
    def _check_sepa_creditor_identifier(self):
        for company in self:
            if company.sepa_creditor_identifier:
                if not is_sepa_creditor_identifier_valid(
                    company.sepa_creditor_identifier
                ):
                    raise ValidationError(
                        _("The SEPA Creditor Identifier '%s' is invalid.")
                        % company.sepa_creditor_identifier
                    )
