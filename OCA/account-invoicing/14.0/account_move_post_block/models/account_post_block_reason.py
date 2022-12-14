# Copyright 2021 ForgeFlow (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/AGPL.html).

from odoo import fields, models


class AccountPostBlockReason(models.Model):
    _name = "account.post.block.reason"
    _description = "Account Post Block Reason"

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
