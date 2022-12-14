# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import SavepointCase


class TestSaleOrderLinePackagingQty(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.precision = cls.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.product = cls.env.ref("product.product_product_9")
        cls.packaging = cls.env["product.packaging"].create(
            {"name": "Test packaging", "product_id": cls.product.id, "qty": 5.0}
        )
        cls.packaging2 = cls.env["product.packaging"].create(
            {"name": "Test packaging", "product_id": cls.product.id, "qty": 2.2}
        )

    def test_product_packaging_qty(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 3.0,
            }
        )
        order_line.write({"product_packaging": self.packaging.id})
        order_line._onchange_product_packaging()
        self.assertAlmostEqual(
            order_line.product_uom_qty, self.packaging.qty, places=self.precision
        )
        self.assertAlmostEqual(
            order_line.product_packaging_qty, 1.0, places=self.precision
        )
        pack_qty = 3.0
        order_line.write({"product_packaging_qty": pack_qty})
        order_line._compute_product_packaging_qty()
        self.assertAlmostEqual(
            order_line.product_uom_qty,
            self.packaging.qty * pack_qty,
            places=self.precision,
        )
        self.assertAlmostEqual(
            order_line.product_packaging_qty, pack_qty, places=self.precision
        )

    def test_product_packaging_qty_float(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 7,
            }
        )
        order_line.write({"product_packaging": self.packaging2.id})
        order_line._onchange_product_packaging()
        self.assertAlmostEqual(
            order_line.product_uom_qty, self.packaging2.qty, places=self.precision
        )
        self.assertAlmostEqual(
            order_line.product_packaging_qty, 1.0, places=self.precision
        )
        pack_qty = 7
        order_line.write({"product_packaging_qty": pack_qty})
        # Via interface, this compute is triggered and could cause some issue.
        # So simulate it.
        order_line._compute_product_packaging_qty()
        self.assertAlmostEqual(
            order_line.product_uom_qty,
            self.packaging2.qty * pack_qty,
            places=self.precision,
        )
        self.assertAlmostEqual(
            order_line.product_packaging_qty, pack_qty, places=self.precision
        )
