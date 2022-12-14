# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_view_purchase_order(self):
        """This function returns an action that display existing purchase order
        of given picking.
        """
        self.ensure_one()
        xmlid = "purchase.purchase_form_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        form = self.env.ref("purchase.purchase_order_form")
        action["views"] = [(form.id, "form")]
        action["res_id"] = self.purchase_id.id
        return action
