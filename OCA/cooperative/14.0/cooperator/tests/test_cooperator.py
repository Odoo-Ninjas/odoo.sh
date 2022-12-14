# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime, timedelta

from odoo.exceptions import AccessError
from odoo.fields import Date
from odoo.tests.common import SavepointCase, users

from .cooperator_test_mixin import CooperatorTestMixin


class CooperatorCase(SavepointCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.share_line = cls.env["share.line"].create(
            {
                "share_product_id": cls.share_x.id,
                "share_number": 2,
                "share_unit_price": 50,
                "partner_id": cls.demo_partner.id,
                "effective_date": datetime.now() - timedelta(days=120),
            }
        )

    @users("user-cooperator")
    def test_put_on_waiting_list(self):
        self.subscription_request_1.put_on_waiting_list()
        self.assertEqual(self.subscription_request_1.state, "waiting")

    @users("user-cooperator")
    def test_validate_subscription_request(self):
        self.subscription_request_1.validate_subscription_request()

        self.assertEqual(self.subscription_request_1.state, "done")
        self.assertTrue(self.subscription_request_1.partner_id)
        self.assertTrue(self.subscription_request_1.partner_id.coop_candidate)
        self.assertFalse(self.subscription_request_1.partner_id.member)
        self.assertEqual(self.subscription_request_1.type, "new")
        self.assertTrue(len(self.subscription_request_1.capital_release_request) >= 1)
        self.assertEqual(
            self.subscription_request_1.capital_release_request.state, "posted"
        )

    @users("user-cooperator")
    def test_capital_release_request_name(self):
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.assertEqual(
            invoice.name,
            "SUBJ/{year}/001".format(year=date.today().year),
        )

    @users("user-cooperator")
    def test_register_payment_for_capital_release(self):
        self.validate_subscription_request_and_pay(self.subscription_request_1)
        invoice = self.subscription_request_1.capital_release_request
        self.assertEqual(invoice.state, "posted")

        partner = self.subscription_request_1.partner_id
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)
        self.assertTrue(partner.share_ids)
        self.assertEqual(partner.effective_date, Date.today())

        share = partner.share_ids[0]
        self.assertEqual(share.share_number, self.subscription_request_1.ordered_parts)
        self.assertEqual(
            share.share_product_id, self.subscription_request_1.share_product_id
        )
        self.assertEqual(share.effective_date, Date.today())

    @users("user-cooperator")
    def test_effective_date_from_payment_date(self):
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.pay_invoice(invoice, date(2022, 6, 21))

        partner = self.subscription_request_1.partner_id
        self.assertEqual(partner.effective_date, date(2022, 6, 21))

    @users("user-cooperator")
    def test_effective_date_from_account_move_date(self):
        # the effective date should also work with an account.move without an
        # account.payment.
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        self.create_payment_account_move(invoice, date(2022, 6, 21))
        partner = self.subscription_request_1.partner_id
        self.assertEqual(partner.effective_date, date(2022, 6, 21))

    @users("user-cooperator")
    def test_effective_date_from_multiple_moves(self):
        # the effective date should come from the most recent account.move.
        self.subscription_request_1.validate_subscription_request()
        invoice = self.subscription_request_1.capital_release_request
        amount = invoice.line_ids[0].credit / 2
        self.create_payment_account_move(invoice, date(2022, 6, 18), amount)
        self.create_payment_account_move(invoice, date(2022, 6, 21), amount)
        partner = self.subscription_request_1.partner_id
        self.assertEqual(partner.effective_date, date(2022, 6, 21))

    @users("demo")
    def test_user_access_rules(self):
        user_demo = self.env.ref("base.user_demo")
        # class object was loaded with root user and its rights
        # so we need to reload it with demo user rights
        request_as_user = self.subscription_request_1.with_user(user_demo)
        with self.assertRaises(AccessError):
            request_as_user.name = "test write request"
        with self.assertRaises(AccessError):
            create_values = self.get_dummy_subscription_requests_vals()
            self.env["subscription.request"].create(create_values)
        with self.assertRaises(AccessError):
            request_as_user.unlink()

        share_line_as_user = self.share_line.with_user(user_demo)
        with self.assertRaises(AccessError):
            share_line_as_user.share_number = 3

    @users("user-cooperator")
    def test_cooperator_access_rules(self):
        cooperator_user = self.ref("cooperator.res_users_user_cooperator_demo")
        # cf comment in test_user_access_rules
        resquest_as_cooperator = self.subscription_request_1.with_user(cooperator_user)
        resquest_as_cooperator.name = "test write request"
        create_values = self.get_dummy_subscription_requests_vals()
        create_request = self.env["subscription.request"].create(create_values)
        with self.assertRaises(AccessError):
            create_request.unlink()

        share_line_as_cooperator_user = self.share_line.with_user(cooperator_user)
        share_line_as_cooperator_user.share_number = 3
        with self.assertRaises(AccessError):
            share_line_as_cooperator_user.unlink()

        share_type_as_cooperator_user = self.share_x.with_user(cooperator_user)
        share_type_as_cooperator_user.list_price = 30
        with self.assertRaises(AccessError):
            self.env["product.template"].create(
                {
                    "name": "Part C - Client",
                    "short_name": "Part C",
                    "is_share": True,
                    "list_price": 50,
                }
            )
        with self.assertRaises(AccessError):
            share_type_as_cooperator_user.unlink()

    @users("manager-cooperator")
    def test_cooperator_manager_access_rules(self):
        cooperator_manager = self.ref("cooperator.res_users_manager_cooperator_demo")
        # cf comment in test_user_access_rules
        request_as_cooperator_manager = self.subscription_request_1.with_user(
            cooperator_manager
        )
        request_as_cooperator_manager.name = "test write request"
        create_values = self.get_dummy_subscription_requests_vals()
        create_request = self.env["subscription.request"].create(create_values)
        with self.assertRaises(AccessError):
            create_request.unlink()

        share_type = self.env["product.template"].create(
            {
                "name": "Part C - Client",
                "short_name": "Part C",
                "is_share": True,
                "list_price": 50,
            }
        )
        share_type.list_price = 30
        share_type.unlink()

    def test_compute_is_valid_iban_on_subscription_request(self):
        self.subscription_request_1.iban = False
        self.subscription_request_1.skip_iban_control = False

        # empty iban - don't skip
        self.assertFalse(self.subscription_request_1.is_valid_iban)

        # good iban - don't skip
        self.subscription_request_1.iban = "BE71096123456769"
        self.assertTrue(self.subscription_request_1.is_valid_iban)

        # wrong iban - don't skip
        self.subscription_request_1.iban = "xxxx"
        self.assertFalse(self.subscription_request_1.is_valid_iban)

        # wrong iban - don't skip
        self.subscription_request_1.iban = "BE71096123456760"
        self.assertFalse(self.subscription_request_1.is_valid_iban)

        # wrong iban - skip
        self.subscription_request_1.skip_iban_control = True
        self.assertTrue(self.subscription_request_1.is_valid_iban)

        # empty iban - skip
        self.subscription_request_1.iban = False
        self.assertTrue(self.subscription_request_1.is_valid_iban)

    def test_create_subscription_from_non_cooperator_partner(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        subscription_request = self.create_dummy_subscription_from_partner(partner)
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.member)
        subscription_request.validate_subscription_request()
        self.assertTrue(partner.cooperator)
        self.assertTrue(partner.coop_candidate)
        self.assertFalse(partner.member)
        self.pay_invoice(subscription_request.capital_release_request)
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)

    def test_create_subscription_from_non_cooperator_company_partner(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "is_company": True,
            }
        )
        subscription_request = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertFalse(partner.member)
        subscription_request.validate_subscription_request()
        self.assertTrue(partner.cooperator)
        self.assertTrue(partner.coop_candidate)
        self.assertFalse(partner.member)
        self.pay_invoice(subscription_request.capital_release_request)
        self.assertTrue(partner.cooperator)
        self.assertFalse(partner.coop_candidate)
        self.assertTrue(partner.member)

    def test_create_multiple_subscriptions_from_non_cooperator_partner(self):
        """
        Test that creating a subscription from a partner that has no parts yet
        creates a subscription request with the correct type.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
            }
        )
        subscription_request = self.create_dummy_subscription_from_partner(partner)
        self.assertEqual(subscription_request.type, "new")
        subscription_request2 = self.create_dummy_subscription_from_partner(partner)
        self.assertEqual(subscription_request2.type, "increase")

    def test_create_multiple_subscriptions_from_non_cooperator_company_partner(self):
        """
        Test that creating a subscription from a company partner that has no
        parts yet creates a subscription request with the correct type.
        """
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "is_company": True,
            }
        )
        subscription_request = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertEqual(subscription_request.type, "new")
        subscription_request2 = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertEqual(subscription_request2.type, "increase")

    def test_create_subscription_from_cooperator_partner(self):
        """
        Test that creating a subscription from a cooperator partner creates a
        subscription request with the correct type.
        """
        partner = self.create_dummy_cooperator()
        subscription_request = self.create_dummy_subscription_from_partner(partner)
        self.assertEqual(subscription_request.type, "increase")

    def test_create_subscription_from_cooperator_company_partner(self):
        """
        Test that creating a subscription from a cooperator company partner
        creates a subscription request with the correct type.
        """
        partner = self.create_dummy_company_cooperator()
        subscription_request = self.create_dummy_subscription_from_company_partner(
            partner
        )
        self.assertEqual(subscription_request.type, "increase")

    def test_create_subscription_without_partner(self):
        subscription_request = self.env["subscription.request"].create(
            self.get_dummy_subscription_requests_vals()
        )
        self.assertEqual(subscription_request.type, "new")
        self.assertEqual(subscription_request.name, "first name last name")
        self.assertFalse(subscription_request.partner_id)
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        self.assertTrue(partner)
        self.assertFalse(partner.is_company)
        self.assertEqual(partner.firstname, "first name")
        self.assertEqual(partner.lastname, "last name")
        self.assertEqual(partner.name, "first name last name")
        self.assertEqual(partner.email, "email@example.net")
        self.assertEqual(partner.phone, "dummy phone")
        self.assertEqual(partner.street, "dummy street")
        self.assertEqual(partner.zip, "dummy zip")
        self.assertEqual(partner.city, "dummy city")
        self.assertEqual(partner.country_id, self.browse_ref("base.be"))
        self.assertEqual(partner.lang, "en_US")
        self.assertEqual(partner.gender, "other")
        self.assertEqual(partner.birthdate_date, date(1980, 1, 1))
        self.assertTrue(partner.cooperator)

    def test_create_subscription_for_company_without_partner(self):
        vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertEqual(subscription_request.type, "new")
        self.assertEqual(subscription_request.name, "dummy company")
        self.assertFalse(subscription_request.partner_id)
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        self.assertTrue(partner)
        self.assertTrue(partner.is_company)
        self.assertFalse(partner.firstname)
        self.assertEqual(partner.lastname, "dummy company")
        self.assertEqual(partner.name, "dummy company")
        self.assertEqual(partner.email, "companyemail@example.net")
        self.assertFalse(partner.phone)
        self.assertEqual(partner.street, "dummy street")
        self.assertEqual(partner.zip, "dummy zip")
        self.assertEqual(partner.city, "dummy city")
        self.assertEqual(partner.country_id, self.browse_ref("base.be"))
        self.assertEqual(partner.lang, "en_US")
        self.assertFalse(partner.gender)
        self.assertFalse(partner.birthdate_date)
        self.assertTrue(partner.cooperator)
        representative = partner.child_ids
        self.assertTrue(representative)
        self.assertFalse(representative.is_company)
        self.assertEqual(representative.type, "representative")
        self.assertEqual(representative.function, "dummy contact person function")
        self.assertEqual(representative.firstname, "first name")
        self.assertEqual(representative.lastname, "last name")
        self.assertEqual(representative.name, "first name last name")
        self.assertEqual(representative.email, "email@example.net")
        self.assertEqual(representative.phone, "dummy phone")
        self.assertEqual(representative.street, "dummy street")
        self.assertEqual(representative.zip, "dummy zip")
        self.assertEqual(representative.city, "dummy city")
        self.assertEqual(representative.country_id, self.browse_ref("base.be"))
        self.assertEqual(representative.lang, "en_US")
        self.assertEqual(representative.gender, "other")
        self.assertEqual(representative.birthdate_date, date(1980, 1, 1))
        # should this be true?
        self.assertTrue(representative.cooperator)

    def test_create_subscription_with_matching_email(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "dummy@example.net",
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = "dummy@example.net"
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertEqual(subscription_request.partner_id, partner)

    def test_create_subscription_with_multiple_matching_email(self):
        self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "dummy@example.net",
            }
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "dummy partner 2",
                "email": "dummy@example.net",
                "cooperator": True,
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = "dummy@example.net"
        subscription_request = self.env["subscription.request"].create(vals)
        # if there are multiple email matches, take the one that is a
        # cooperator.
        self.assertEqual(subscription_request.partner_id, partner2)

    def test_create_subscription_with_matching_empty_email(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "",
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = ""
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertNotEqual(subscription_request.partner_id, partner)

    def test_create_subscription_with_matching_space_email(self):
        partner = self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "",
            }
        )
        vals = self.get_dummy_subscription_requests_vals()
        vals["email"] = " "
        subscription_request = self.env["subscription.request"].create(vals)
        self.assertNotEqual(subscription_request.partner_id, partner)

    def test_create_subscription_with_matching_company_register_number(self):
        # create a dummy person partner to check that the match is not done by
        # email for companies.
        self.env["res.partner"].create(
            {
                "name": "dummy partner 1",
                "email": "dummy@example.net",
            }
        )
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "company_register_number": "dummy company register number",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        vals["email"] = "dummy@example.net"
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertEqual(partner, company_partner)
        # no representative is created
        self.assertFalse(partner.child_ids)

    def test_create_subscription_with_multiple_matching_company_register_number(self):
        self.env["res.partner"].create(
            {
                "name": "dummy company 1",
                "email": "dummycompany@example.net",
                "company_register_number": "dummy company register number",
                "is_company": True,
            }
        )
        company_partner2 = self.env["res.partner"].create(
            {
                "name": "dummy company 2",
                "email": "dummycompany@example.net",
                "company_register_number": "dummy company register number",
                "is_company": True,
                "cooperator": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        # if there are multiple company register number matches, take the one
        # that is a cooperator.
        self.assertEqual(partner, company_partner2)

    def test_create_subscription_with_matching_empty_company_register_number(self):
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "company_register_number": "",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        vals["company_register_number"] = ""
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertNotEqual(partner, company_partner)

    def test_create_subscription_with_matching_space_company_register_number(self):
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "company_register_number": "",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        vals["company_register_number"] = " "
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertNotEqual(partner, company_partner)

    def test_create_subscription_with_matching_none_company_register_number(self):
        company_partner = self.env["res.partner"].create(
            {
                "name": "dummy company",
                "email": "dummycompany@example.net",
                "is_company": True,
            }
        )
        vals = self.get_dummy_company_subscription_requests_vals()
        del vals["company_register_number"]
        subscription_request = self.env["subscription.request"].create(vals)
        partner = subscription_request.partner_id
        self.assertNotEqual(partner, company_partner)
