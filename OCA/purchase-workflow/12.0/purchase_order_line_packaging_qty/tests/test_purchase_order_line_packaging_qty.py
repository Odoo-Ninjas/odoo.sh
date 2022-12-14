# Copyright 2020 Camptocamp SA
# Copyright 2020 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields
from odoo.tests import SavepointCase


class TestPurchaseOrderLinePackagingQty(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.product = cls.env.ref("product.product_product_9")
        cls.packaging = cls.env["product.packaging"].create(
            {"name": "Test packaging", "product_id": cls.product.id, "qty": 5.0}
        )

    def test_product_packaging_qty(self):
        order = self.env["purchase.order"].create({"partner_id": self.partner.id})
        order_line = self.env["purchase.order.line"].create(
            {
                "name": self.product.display_name,
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_qty": 3.0,
                "price_unit": 0.0,
                "date_planned": fields.Datetime.today(),
            }
        )
        order_line.write({"product_packaging": self.packaging.id})
        order_line._onchange_product_packaging()
        self.assertEqual(order_line.product_uom_qty, 5.0)
        self.assertEqual(order_line.product_packaging_qty, 1.0)
        order_line.write({"product_packaging_qty": 3.0})
        self.assertEqual(order_line.product_uom_qty, 15.0)
