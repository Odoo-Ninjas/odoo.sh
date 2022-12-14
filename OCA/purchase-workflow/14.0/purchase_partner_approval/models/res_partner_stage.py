# Copyright 2022 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PartnerStage(models.Model):
    _inherit = "res.partner.stage"

    approved_purchase = fields.Boolean(string="Approved for Purchase", default=True)
