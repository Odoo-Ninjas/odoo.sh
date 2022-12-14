# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestPartnerSaleRisk(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create({"name": "Test pricelist"})
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test partner", "property_product_pricelist": cls.pricelist.id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "list_price": 100}
        )
        cls.sale_order = cls._create_sale_order(cls)
        cls.exception_rule_risk_have_risk_message = cls.env.ref(
            "sale_exception_financial_risk.sale_financial_risk_have_risk_message"
        )

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        return order_form.save()

    def test_partner_risk_exception(self):
        self.partner.risk_exception = "Exception"
        self.sale_order.detect_exceptions()
        self.assertTrue(
            self.sale_order.exception_ids.filtered(
                lambda x: x == self.exception_rule_risk_have_risk_message
            )
        )
        self.sale_order.action_confirm()

    def test_risk_exceeds_risk_sale_order_limit(self):
        self.sale_order.action_confirm()
        self.partner.risk_sale_order_limit = 99.0
        sale_order2 = self.sale_order.copy()
        sale_order2.detect_exceptions()
        self.assertTrue(
            sale_order2.exception_ids.filtered(
                lambda x: x == self.exception_rule_risk_have_risk_message
            )
        )
        sale_order2.action_confirm()

    def test_risk_exceeds_credit_limit(self):
        self.sale_order.action_confirm()
        self.partner.risk_sale_order_include = True
        self.partner.credit_limit = 99.0
        sale_order2 = self.sale_order.copy()
        sale_order2.detect_exceptions()
        self.assertTrue(
            sale_order2.exception_ids.filtered(
                lambda x: x == self.exception_rule_risk_have_risk_message
            )
        )
        sale_order2.action_confirm()
