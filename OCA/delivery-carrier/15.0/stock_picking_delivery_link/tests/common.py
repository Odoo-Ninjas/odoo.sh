# Copyright 2020-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class StockPickingDeliveryLinkCommonCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.wh = cls.env.ref("stock.warehouse0")

        cls.stock_loc = cls.wh.lot_stock_id
        cls.shelf1_loc = cls.env.ref("stock.stock_location_components")
        cls.shelf2_loc = cls.env.ref("stock.stock_location_14")

    def _create_move(self, product, src_location, dst_location, **values):
        Move = self.env["stock.move"]
        # simulate create + onchange
        move = Move.new(
            {
                "product_id": product.id,
                "location_id": src_location.id,
                "location_dest_id": dst_location.id,
            }
        )
        move._onchange_product_id()
        move_values = move._convert_to_write(move._cache)
        move_values.update(**values)
        return Move.create(move_values)
