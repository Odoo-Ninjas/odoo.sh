# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestSaleOrder(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order_model = cls.env["sale.order"]
        company = cls.env.company
        company.keep_name_so = False

    def test_enumeration(self):
        order1 = self.sale_order_model.create(
            {"partner_id": self.env.ref("base.res_partner_1").id}
        )
        quotation1_name = order1.name
        order2 = self.sale_order_model.create(
            {"partner_id": self.env.ref("base.res_partner_1").id}
        )
        quotation2_name = order2.name

        self.assertRegexpMatches(quotation1_name, "SQ")
        self.assertRegexpMatches(quotation2_name, "SQ")
        self.assertLess(int(quotation1_name[2:]), int(quotation2_name[2:]))

        order2.action_confirm()
        order1.action_confirm()

        self.assertRegexpMatches(order1.name, "S")
        self.assertEqual(order1.origin, quotation1_name)

        self.assertRegexpMatches(order2.name, "S")
        self.assertEqual(order2.origin, quotation2_name)
        self.assertLess(int(order2.name[1:]), int(order1.name[1:]))

    def test_with_origin(self):
        origin = "origin"
        order1 = self.sale_order_model.create(
            {"origin": origin, "partner_id": self.env.ref("base.res_partner_1").id}
        )
        quotation1_name = order1.name
        order1.action_confirm()

        self.assertRegexpMatches(order1.name, "S")
        self.assertEqual(order1.origin, ", ".join([origin, quotation1_name]))

    def test_copy_no_origin(self):
        order1 = self.sale_order_model.create(
            {"partner_id": self.env.ref("base.res_partner_1").id}
        )
        order_copy = order1.copy()

        self.assertEqual(order1.name, order_copy.origin)

    def test_copy_with_origin(self):
        origin = "origin"
        vals = {"origin": origin, "partner_id": self.env.ref("base.res_partner_1").id}
        # This test fails randomly if sale_order_revision is installed so I
        # apply this trick
        if "unrevisioned_name" in self.sale_order_model:
            vals["unrevisioned_name"] = "URunrevisioned_name_01"
        order1 = self.sale_order_model.create(vals)
        order_copy = order1.copy()

        self.assertEqual(", ".join([origin, order1.name]), order_copy.origin)

    def test_error_confirmation_sequence(self):
        order = self.sale_order_model.create(
            {"partner_id": self.env.ref("base.res_partner_1").id, "state": "done"}
        )
        # An exception is forced
        sequence_id = self.env["ir.sequence"].search(
            [
                ("code", "=", "sale.order"),
                ("company_id", "in", [order.company_id.id, False]),
            ]
        )
        next_name = sequence_id.get_next_char(sequence_id.number_next_actual)
        try:
            order.action_confirm()
        except UserError:
            pass
        order.update({"state": "draft"})
        # Now the SQ can be confirmed
        order.action_confirm()
        self.assertEqual(next_name, order.name)
