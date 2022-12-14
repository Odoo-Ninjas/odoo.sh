# Copyright 2018 Tecnativa - Ernesto tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import base
from odoo.exceptions import ValidationError


class MailMassMailingListCase(base.BaseCase):

    def test_create_mass_mailing_list(self):
        contact_test_1 = self.create_mailing_contact({
            'name': 'Contact test 1',
            'partner_id': self.partner.id,
        })
        contact_test_2 = self.create_mailing_contact({
            'name': 'Contact test 2',
            'partner_id': self.partner.id,
        })
        with self.assertRaises(ValidationError):
            self.create_mailing_list({
                'name': 'List test Create Mailing List',
                'contact_ids': [(6, 0, (contact_test_1 | contact_test_2).ids)]
            })

    def test_create_mass_mailing_list_with_subscription(self):
        contact_test_1 = self.create_mailing_contact({
            'name': 'Contact test 1',
            'partner_id': self.partner.id,
        })
        contact_test_2 = self.create_mailing_contact({
            'name': 'Contact test 2',
            'partner_id': self.partner.id,
        })
        with self.assertRaises(ValidationError):
            self.create_mailing_list({
                'name': 'List test Creat List With Subscription',
                'subscription_contact_ids': [
                    (0, 0, {'contact_id': contact_test_1.id}),
                    (0, 0, {'contact_id': contact_test_2.id}),
                ]
            })
