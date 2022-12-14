# Copyright 2017-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestTaxInvoiceBasis(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env.user.company_id.country_id = self.env.ref("base.nl")

        self.tax = self.env["account.tax"].create(
            {"name": "Tax 21.0%", "amount": 21.0, "amount_type": "percent"}
        )
        invoice_line_account_id = (
            self.env["account.account"]
            .search(
                [
                    (
                        "user_type_id",
                        "=",
                        self.env.ref("account.data_account_type_expenses").id,
                    )
                ],
                limit=1,
            )
            .id
        )
        invoice = self.env["account.move"].create(
            {
                "type": "in_invoice",
                "partner_id": self.env.ref("base.res_partner_4").id,
                "invoice_date": "2017-08-18",
                "date": "2017-07-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("base.res_partner_4").id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "account_id": invoice_line_account_id,
                            "tax_ids": [(6, 0, [self.tax.id])],
                        },
                    )
                ],
            }
        )
        invoice.flush()
        self.period_july = {"from_date": "2017-07-01", "to_date": "2017-07-31"}
        self.period_august = {"from_date": "2017-08-01", "to_date": "2017-08-31"}
        self.invoice = invoice

    def test_01_tax_invoice_basis(self):

        company = self.env.user.company_id
        # Factuurstelsel enabled by default
        self.assertTrue(company.l10n_nl_tax_invoice_basis)

        # Validate invoice
        self.invoice.action_post()

        tax_july = self.tax.with_context(self.period_july)
        tax_july._compute_balance()

        self.assertEqual(tax_july.base_balance, 0.0)
        self.assertEqual(tax_july.balance, 0.0)
        self.assertEqual(tax_july.base_balance_regular, 0.0)
        self.assertEqual(tax_july.balance_regular, 0.0)
        self.assertEqual(tax_july.base_balance_refund, 0.0)
        self.assertEqual(tax_july.balance_refund, 0.0)

        tax_august = self.tax.with_context(self.period_august)
        tax_august._compute_balance()

        self.assertEqual(tax_august.base_balance, -100.0)
        self.assertEqual(tax_august.balance, -21.0)
        self.assertEqual(tax_august.base_balance_regular, -100.0)
        self.assertEqual(tax_august.balance_regular, -21.0)
        self.assertEqual(tax_august.base_balance_refund, 0.0)
        self.assertEqual(tax_august.balance_refund, 0.0)

    def test_02_tax_standard(self):

        # Factuurstelsel disabled
        self.env.user.company_id.l10n_nl_tax_invoice_basis = False

        # Validate invoice
        self.invoice.action_post()

        tax_july = self.tax.with_context(self.period_july)

        self.assertEqual(tax_july.base_balance, -100.0)
        self.assertEqual(tax_july.balance, -21.0)
        self.assertEqual(tax_july.base_balance_regular, -100.0)
        self.assertEqual(tax_july.balance_regular, -21.0)
        self.assertEqual(tax_july.base_balance_refund, 0.0)
        self.assertEqual(tax_july.balance_refund, 0.0)

        tax_august = self.tax.with_context(self.period_august)
        tax_august._compute_balance()

        self.assertEqual(tax_august.base_balance, 0.0)
        self.assertEqual(tax_august.balance, 0.0)
        self.assertEqual(tax_august.base_balance_regular, 0.0)
        self.assertEqual(tax_august.balance_regular, 0.0)
        self.assertEqual(tax_august.base_balance_refund, 0.0)
        self.assertEqual(tax_august.balance_refund, 0.0)

    def test_03_skip_by_context(self):

        # Factuurstelsel configured as enabled
        # but context is used to skip the functionality
        update_ctx = {"skip_invoice_basis_domain": True}
        self.period_july.update(update_ctx)
        self.period_august.update(update_ctx)

        # Validate invoice
        self.invoice.action_post()

        tax_july = self.tax.with_context(self.period_july)

        self.assertEqual(tax_july.base_balance, -100.0)
        self.assertEqual(tax_july.balance, -21.0)
        self.assertEqual(tax_july.base_balance_regular, -100.0)
        self.assertEqual(tax_july.balance_regular, -21.0)
        self.assertEqual(tax_july.base_balance_refund, 0.0)
        self.assertEqual(tax_july.balance_refund, 0.0)

        tax_august = self.tax.with_context(self.period_august)
        tax_august._compute_balance()

        self.assertEqual(tax_august.base_balance, 0.0)
        self.assertEqual(tax_august.balance, 0.0)
        self.assertEqual(tax_august.base_balance_regular, 0.0)
        self.assertEqual(tax_august.balance_regular, 0.0)
        self.assertEqual(tax_august.base_balance_refund, 0.0)
        self.assertEqual(tax_august.balance_refund, 0.0)

    def test_04_tax_no_nl(self):
        # company is not Netherlands
        self.env.user.company_id.country_id = self.env.ref("base.be")

        company = self.env.user.company_id
        # Factuurstelsel enabled by default
        self.assertTrue(company.l10n_nl_tax_invoice_basis)

        # Validate invoice
        self.invoice.action_post()

        tax_july = self.tax.with_context(self.period_july)

        self.assertEqual(tax_july.base_balance, -100.0)
        self.assertEqual(tax_july.balance, -21.0)
        self.assertEqual(tax_july.base_balance_regular, -100.0)
        self.assertEqual(tax_july.balance_regular, -21.0)
        self.assertEqual(tax_july.base_balance_refund, 0.0)
        self.assertEqual(tax_july.balance_refund, 0.0)

        tax_august = self.tax.with_context(self.period_august)
        tax_august._compute_balance()

        self.assertEqual(tax_august.base_balance, 0.0)
        self.assertEqual(tax_august.balance, 0.0)
        self.assertEqual(tax_august.base_balance_regular, 0.0)
        self.assertEqual(tax_august.balance_regular, 0.0)
        self.assertEqual(tax_august.base_balance_refund, 0.0)
        self.assertEqual(tax_august.balance_refund, 0.0)
