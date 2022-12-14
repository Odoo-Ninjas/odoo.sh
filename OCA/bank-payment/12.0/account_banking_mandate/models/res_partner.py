# Copyright 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2017-2021 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.fields import first


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mandate_count = fields.Integer(
        compute='_compute_mandate_count', string="Number of Mandates",
        readonly=True)
    valid_mandate_id = fields.Many2one(
        comodel_name='account.banking.mandate',
        compute='_compute_valid_mandate_id',
        string='First Valid Mandate')

    @api.multi
    def _compute_mandate_count(self):
        mandate_data = self.env['account.banking.mandate'].read_group(
            [('partner_id', 'in', self.ids)], ['partner_id'], ['partner_id'])
        mapped_data = dict([
            (mandate['partner_id'][0], mandate['partner_id_count'])
            for mandate in mandate_data])
        for partner in self:
            partner.mandate_count = mapped_data.get(partner.id, 0)

    def _get_first_valid_mandate(self, partner_bank_id=False):
        self.ensure_one()
        company_id = self.env.context.get('force_company', False)
        if company_id:
            company = self.env['res.company'].browse(company_id)
        else:
            company = self.env['res.company']._company_default_get(
                'account.banking.mandate')
        mandates = self.commercial_partner_id.bank_ids.mapped('mandate_ids')
        mandates = mandates.filtered(
            lambda x: x.state == 'valid' and x.company_id == company)
        if partner_bank_id:
            mandates = mandates.filtered(
                lambda m: m.partner_bank_id.id == partner_bank_id) or mandates
        return first(mandates)

    @api.multi
    def _compute_valid_mandate_id(self):
        # Dict for reducing the duplicated searches on parent/child partners
        mandates_dic = {}
        for partner in self:
            commercial_partner_id = partner.commercial_partner_id.id
            if commercial_partner_id in mandates_dic:
                partner.valid_mandate_id = mandates_dic[commercial_partner_id]
            else:
                first_valid_mandate_id = partner._get_first_valid_mandate()
                partner.valid_mandate_id = first_valid_mandate_id
                mandates_dic[commercial_partner_id] = first_valid_mandate_id
