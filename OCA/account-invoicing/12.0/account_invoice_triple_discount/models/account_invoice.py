# Copyright 2017 Tecnativa - David Vidal
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def get_taxes_values(self):
        vals = {}
        digits = self.invoice_line_ids._fields['price_unit']._digits
        self.invoice_line_ids._fields['price_unit']._digits = (16, 16)
        for line in self.invoice_line_ids:
            vals[line] = {
                'price_unit': line.price_unit,
                'discount': line.discount,
            }
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price_unit *= (1 - (line.discount2 or 0.0) / 100.0)
            price_unit *= (1 - (line.discount3 or 0.0) / 100.0)
            line.update({
                'price_unit': price_unit,
                'discount': 0.0,
            })
        self.invoice_line_ids._fields['price_unit']._digits = digits
        tax_grouped = super(AccountInvoice, self).get_taxes_values()
        for line in self.invoice_line_ids:
            line.update(vals[line])
        return tax_grouped


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount2 = fields.Float(
        'Discount 2 (%)',
        digits=dp.get_precision('Discount'),
    )
    discount3 = fields.Float(
        'Discount 3 (%)',
        digits=dp.get_precision('Discount'),
    )

    @api.multi
    @api.depends('discount2', 'discount3')
    def _compute_price(self):
        digits = self._fields['price_unit']._digits
        for line in self:
            prev_price_unit = line.price_unit
            prev_discount = line.discount
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price_unit *= (1 - (line.discount2 or 0.0) / 100.0)
            price_unit *= (1 - (line.discount3 or 0.0) / 100.0)
            line._fields['price_unit']._digits = (16, 16)
            line.update({
                'price_unit': price_unit,
                'discount': 0.0,
            })
            line._fields['price_unit']._digits = digits
            super(AccountInvoiceLine, line)._compute_price()
            line.update({
                'price_unit': prev_price_unit,
                'discount': prev_discount,
            })
