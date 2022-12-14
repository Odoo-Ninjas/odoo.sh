# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase


class TestSaleMarginSync(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Pricelist for testing sale_margin_sync"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.product = cls.env["product.product"].create(
            {"name": "test_product", "type": "product", "standard_price": 70}
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "quantity": 30.0,
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": 100.00,
                        },
                    )
                ],
                "pricelist_id": cls.pricelist.id,
            }
        )

    def test_sale_margin_sync(self):
        self.order.action_confirm()
        so_line = self.order.order_line[:1]
        move = so_line.move_ids[:1]
        move.quantity_done = 10
        move.picking_id.action_done()
        move.stock_valuation_layer_ids[:1].unit_cost = 80.0
        self.assertEqual(so_line.purchase_price, 80.0)
        self.assertEqual(so_line.margin, 200.0)

    def test_sale_margin_sync_unvalidated_move(self):
        self.order.action_confirm()
        so_line = self.order.order_line[:1]
        move = so_line.move_ids[:1]
        move.quantity_done = 10
        move.stock_valuation_layer_ids[:1].unit_cost = 80.0
        self.assertEqual(so_line.purchase_price, 70.0)
        self.assertEqual(so_line.margin, 300.0)
