# Copyright 2014-2021 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Provide an interface to approach any relation from two points of view."""
# pylint: disable=no-self-use,protected-access
import collections
import json
import logging

from psycopg2.extensions import AsIs

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, ValidationError
from odoo.tools import drop_view_if_exists


_logger = logging.getLogger(__name__)


# Register relations
RELATIONS_SQL = """\
SELECT
    (rel.id * %%(padding)s) + %(key_offset)s AS id,
    'res.partner.relation' AS res_model,
    rel.id AS res_id,
    rel.left_partner_id AS this_partner_id,
    rel.right_partner_id AS other_partner_id,
    rel.type_id,
    rel.date_start,
    rel.date_end,
    %(is_inverse)s as is_inverse
    %(extra_additional_columns)s
FROM res_partner_relation rel"""

# Register inverse relations
RELATIONS_SQL_INVERSE = """\
SELECT
    (rel.id * %%(padding)s) + %(key_offset)s AS id,
    'res.partner.relation',
    rel.id,
    rel.right_partner_id,
    rel.left_partner_id,
    rel.type_id,
    rel.date_start,
    rel.date_end,
    %(is_inverse)s as is_inverse
    %(extra_additional_columns)s
FROM res_partner_relation rel"""


class ResPartnerRelationAll(models.AbstractModel):
    """Abstract model to show each relation from two sides."""

    _auto = False
    _log_access = False
    _name = "res.partner.relation.all"
    _description = "All (non-inverse + inverse) relations between partners"
    _order = "this_partner_id, type_selection_id, date_end desc, date_start desc"

    @api.multi
    def _compute_active(self):
        """active is computed based on end-date."""
        today = fields.Date.today()
        for this in self:
            if this.date_end and this.date_end <= today:
                this.active = False
                continue
            this.active = True

    def _search_active(self, operator, value):
        """Return domain using date_start and date_end."""
        assert value in (True, False)
        if operator in ("!=", "<>"):
            value = not value
        today = fields.Date.today()
        if value:  # Find active records.
            return [
                "&",
                "|",
                ("date_start", "=", False),
                ("date_start", "<=", today),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", today),
            ]
        # Find not active records.
        return [
            "|",
            ("date_start", ">", today),
            ("date_end", "<", today),
        ]

    res_model = fields.Char(
        string="Resource Model",
        readonly=True,
        required=True,
        help="The database object this relation is based on.",
    )
    res_id = fields.Integer(
        string="Resource ID",
        readonly=True,
        required=True,
        help="The id of the object in the model this relation is based on.",
    )
    this_partner_id = fields.Many2one(
        comodel_name="res.partner", string="One Partner", required=True
    )
    other_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Other Partner", required=True
    )
    type_id = fields.Many2one(
        comodel_name="res.partner.relation.type",
        string="Underlying Relation Type",
        readonly=True,
        required=True,
    )
    date_start = fields.Date("Starting date")
    date_end = fields.Date("Ending date")
    is_inverse = fields.Boolean(
        string="Is reverse type?",
        readonly=True,
        help="Inverse relations are from right to left partner.",
    )
    type_selection_id = fields.Many2one(
        comodel_name="res.partner.relation.type.selection",
        string="Relation Type",
        required=True,
    )
    active = fields.Boolean(
        string="Active",
        compute="_compute_active",
        search="_search_active",
        readonly=True,
        help="Records with date_end in the past are inactive",
    )
    any_partner_id = fields.Many2many(
        comodel_name="res.partner",
        string="Partner",
        compute=lambda self: None,
        search="_search_any_partner_id",
    )
    # Helper fields to set domain
    this_partner_id_domain = fields.Char(
        compute="_compute_domains", readonly=True, store=False
    )
    type_selection_id_domain = fields.Char(
        compute="_compute_domains", readonly=True, store=False
    )
    other_partner_id_domain = fields.Char(
        compute="_compute_domains", readonly=True, store=False
    )

    @api.multi
    @api.depends("this_partner_id", "type_selection_id", "other_partner_id")
    def _compute_domains(self):
        def json_dump(this, result, fieldname):
            this["%s_domain" % fieldname] = json.dumps(result["domain"][fieldname])

        for this in self:
            result = this.onchange_type_selection_id()
            json_dump(this, result, "this_partner_id")
            json_dump(this, result, "other_partner_id")
            result = this.onchange_partner_id()
            json_dump(this, result, "type_selection_id")

    def register_specification(self, register, base_name, is_inverse, select_sql):
        """To support adding extra records not based on res.partner.relation."""
        _last_key_offset = register["_lastkey"]
        key_name = base_name + (is_inverse and "_inverse" or "")
        assert key_name not in register
        assert "%%(padding)s" in select_sql
        assert "%(key_offset)s" in select_sql
        assert "%(is_inverse)s" in select_sql
        _last_key_offset += 1
        register["_lastkey"] = _last_key_offset
        register[key_name] = dict(
            base_name=base_name,
            is_inverse=is_inverse,
            key_offset=_last_key_offset,
            select_sql=select_sql
            % {
                "key_offset": _last_key_offset,
                "is_inverse": is_inverse,
                "extra_additional_columns": self._get_additional_relation_columns(),
            },
        )

    def get_register(self):
        """The register contains one entry for each kind of relation."""
        register = collections.OrderedDict()
        register["_lastkey"] = -1
        self.register_specification(register, "relation", False, RELATIONS_SQL)
        self.register_specification(register, "relation", True, RELATIONS_SQL_INVERSE)
        return register

    def get_select_specification(self, base_name, is_inverse):
        """Get the key for the kind of relation in the registry."""
        register = self.get_register()
        key_name = base_name + (is_inverse and "_inverse" or "")
        return register[key_name]

    def _get_statement(self):
        """Allow other modules to add to statement."""
        register = self.get_register()
        union_select = " UNION ".join(
            [register[key]["select_sql"] for key in register if key != "_lastkey"]
        )
        return """\
CREATE OR REPLACE VIEW %%(table)s AS
     WITH base_selection AS (%(union_select)s)
 SELECT
     bas.*,
     CASE
         WHEN NOT bas.is_inverse OR typ.is_symmetric
         THEN bas.type_id * 2
         ELSE (bas.type_id * 2) + 1
     END as type_selection_id,
     (bas.date_end IS NULL OR bas.date_end >= current_date) AS active
     %%(additional_view_fields)s
 FROM base_selection bas
 JOIN res_partner_relation_type typ ON (bas.type_id = typ.id)
 %%(additional_tables)s
        """ % {
            "union_select": union_select
        }

    def _get_padding(self):
        """Utility function to define padding in one place."""
        # pylint: disable=no-self-use
        return 100

    def _get_additional_relation_columns(self):
        """Get additionnal columns from res_partner_relation.

        This allows to add fields to the model res.partner.relation
        and display these fields in the res.partner.relation.all list view.

        :return: ', rel.column_a, rel.column_b_id'
        """
        return ""

    def _get_additional_view_fields(self):
        """Allow inherit models to add fields to view.

        If fields are added, the resulting string must have each field
        prepended by a comma, like so:
            return ', typ.allow_self, typ.left_partner_category'
        """
        # pylint: disable=no-self-use
        return ""

    def _get_additional_tables(self):
        """Allow inherit models to add tables (JOIN's) to view.

        Example:
            return 'JOIN type_extention ext ON (bas.type_id = ext.id)'
        """
        # pylint: disable=no-self-use
        return ""

    @api.model_cr_context
    def _auto_init(self):
        cr = self._cr  # pylint: disable=invalid-name
        drop_view_if_exists(cr, self._table)
        cr.execute(
            self._get_statement(),
            {
                "table": AsIs(self._table),
                "padding": self._get_padding(),
                "additional_view_fields": AsIs(self._get_additional_view_fields()),
                "additional_tables": AsIs(self._get_additional_tables()),
            },
        )
        return super()._auto_init()

    @api.model
    def _search_any_partner_id(self, operator, value):
        """Search relation with partner, no matter on which side."""
        # pylint: disable=no-self-use
        return [
            "|",
            ("this_partner_id", operator, value),
            ("other_partner_id", operator, value),
        ]

    @api.multi
    def name_get(self):
        return {
            this.id: "%s %s %s"
            % (
                this.this_partner_id.name,
                this.type_selection_id.display_name,
                this.other_partner_id.name,
            )
            for this in self
        }

    @api.onchange("type_selection_id")
    def onchange_type_selection_id(self):
        """Add domain on partners according to category and contact_type."""

        def check_partner_domain(partner, partner_domain, side):
            """Check wether partner_domain results in empty selection
            for partner, or wrong selection of partner already selected.
            """
            warning = {}
            if partner:
                test_domain = [("id", "=", partner.id)] + partner_domain
            else:
                test_domain = partner_domain
            partner_model = self.env["res.partner"]
            partners_found = partner_model.search(test_domain, limit=1)
            if not partners_found:
                warning["title"] = _("Error!")
                if partner:
                    warning["message"] = (
                        _("%s partner incompatible with relation type.") % side.title()
                    )
                else:
                    warning["message"] = (
                        _("No %s partner available for relation type.") % side
                    )
            return warning

        # For the moment only support relations between contact partners.
        # We might make this more flexible in the future, but then we would
        # need to add the allowed contact types to the definition of the
        # relation type.
        this_partner_domain = [("type", "=", "contact")]
        other_partner_domain = [("type", "=", "contact")]
        if self.type_selection_id.contact_type_this:
            this_partner_domain.append(
                ("is_company", "=", self.type_selection_id.contact_type_this == "c")
            )
        if self.type_selection_id.partner_category_this:
            this_partner_domain.append(
                ("category_id", "in", self.type_selection_id.partner_category_this.ids)
            )
        if self.type_selection_id.contact_type_other:
            other_partner_domain.append(
                ("is_company", "=", self.type_selection_id.contact_type_other == "c")
            )
        if self.type_selection_id.partner_category_other:
            other_partner_domain.append(
                ("category_id", "in", self.type_selection_id.partner_category_other.ids)
            )
        result = {
            "domain": {
                "this_partner_id": this_partner_domain,
                "other_partner_id": other_partner_domain,
            }
        }
        # Check wether domain results in no choice or wrong choice of partners:
        warning = {}
        partner_model = self.env["res.partner"]
        if this_partner_domain:
            this_partner = False
            if bool(self.this_partner_id.id):
                this_partner = self.this_partner_id
            else:
                this_partner_id = self.env.context.get(
                    "default_this_partner_id", self.env.context.get("active_id", False)
                )
                if this_partner_id:
                    this_partner = partner_model.browse(this_partner_id)
            warning = check_partner_domain(this_partner, this_partner_domain, _("this"))
        if not warning and other_partner_domain:
            warning = check_partner_domain(
                self.other_partner_id, other_partner_domain, _("other")
            )
        if warning:
            result["warning"] = warning
        return result

    @api.onchange("this_partner_id", "other_partner_id")
    def onchange_partner_id(self):
        """Set domain on type_selection_id based on partner(s) selected."""

        def check_type_selection_domain(type_selection_domain):
            """If type_selection_id already selected, check wether it
            is compatible with the computed type_selection_domain. An empty
            selection can practically only occur in a practically empty
            database, and will not lead to problems. Therefore not tested.
            """
            warning = {}
            if not (type_selection_domain and self.type_selection_id):
                return warning
            test_domain = [
                ("id", "=", self.type_selection_id.id)
            ] + type_selection_domain
            type_model = self.env["res.partner.relation.type.selection"]
            types_found = type_model.search(test_domain, limit=1)
            if not types_found:
                warning["title"] = _("Error!")
                warning["message"] = _(
                    "Relation type incompatible with selected partner(s)."
                )
            return warning

        type_selection_domain = []
        if self.this_partner_id:
            type_selection_domain += [
                "|",
                ("contact_type_this", "=", False),
                ("contact_type_this", "=", self.this_partner_id.get_partner_type()),
                "|",
                ("partner_category_this", "=", False),
                ("partner_category_this", "in", self.this_partner_id.category_id.ids),
            ]
        if self.other_partner_id:
            type_selection_domain += [
                "|",
                ("contact_type_other", "=", False),
                ("contact_type_other", "=", self.other_partner_id.get_partner_type()),
                "|",
                ("partner_category_other", "=", False),
                ("partner_category_other", "in", self.other_partner_id.category_id.ids),
            ]
        result = {"domain": {"type_selection_id": type_selection_domain}}
        # Check wether domain results in no choice or wrong choice for
        # type_selection_id:
        warning = check_type_selection_domain(type_selection_domain)
        if warning:
            result["warning"] = warning
        return result

    @api.model
    def _correct_vals(self, original_vals, type_selection):
        """Fill left and right partner from this and other partner."""
        vals = original_vals.copy()
        context = self.env.context
        if "type_selection_id" in vals:
            vals["type_id"] = type_selection.type_id.id
        if type_selection.is_inverse:
            vals["right_partner_id"] = original_vals.get(
                "this_partner_id", self.this_partner_id.id or context.get("active_id")
            )
            vals["left_partner_id"] = vals.get(
                "other_partner_id", self.other_partner_id.id
            )
        else:
            vals["left_partner_id"] = original_vals.get(
                "this_partner_id", self.this_partner_id.id or context.get("active_id")
            )
            vals["right_partner_id"] = vals.get(
                "other_partner_id", self.other_partner_id.id
            )
        # Delete values not in underlying table:
        for key in (
            "this_partner_id",
            "type_selection_id",
            "other_partner_id",
            "this_partner_id_domain",
            "type_selection_id_domain",
            "other_partner_id_domain",
            "is_inverse",
        ):
            if key in vals:
                del vals[key]
        return vals

    @api.multi
    def get_base_resource(self):
        """Get base resource from res_model and res_id."""
        self.ensure_one()
        base_model = self.env[self.res_model]
        return base_model.browse([self.res_id])

    @api.multi
    def write_resource(self, base_resource, vals):
        """write handled by base resource."""
        self.ensure_one()
        # write for models other then res.partner.relation SHOULD
        # be handled in inherited models:
        relation_model = self.env["res.partner.relation"]
        assert self.res_model == relation_model._name
        base_resource.write(vals)

    @api.model
    def _get_type_selection_from_vals(self, vals):
        """Get type_selection_id straight from vals or compute from type_id."""
        type_selection_id = vals.get("type_selection_id", False)
        if not type_selection_id:
            type_id = vals.get("type_id", False)
            if type_id:
                is_inverse = vals.get("is_inverse")
                type_selection_id = type_id * 2 + (is_inverse and 1 or 0)
        return (
            self.type_selection_id.browse(type_selection_id)
            if type_selection_id
            else False
        )

    # pylint: disable=method-required-super
    @api.multi
    def write(self, vals):
        """For model 'res.partner.relation' call write on underlying model."""
        if "active" in vals:
            active = vals.pop("active")
            if active:
                vals["date_end"] = False
            else:
                vals["date_end"] = fields.Date.today()
        new_type_selection = self._get_type_selection_from_vals(vals)
        for this in self:
            type_selection = new_type_selection or this.type_selection_id
            vals = this._correct_vals(vals, type_selection)
            base_resource = this.get_base_resource()
            this.write_resource(base_resource, vals)
        # Invalidate cache to make res.partner.relation.all reflect changes
        # in underlying res.partner.relation:
        self.env.clear()
        return True

    @api.model
    def _compute_base_name(self, type_selection):
        """This will be overridden for each inherit model."""
        # pylint: disable=unused-argument
        return "relation"

    @api.model
    def _compute_id(self, base_resource, type_selection):
        """Compute id. Allow for enhancements in inherit model."""
        base_name = self._compute_base_name(type_selection)
        key_offset = self.get_select_specification(
            base_name, type_selection.is_inverse
        )["key_offset"]
        return base_resource.id * self._get_padding() + key_offset

    @api.model
    def create_resource(self, vals, type_selection):
        """Create the underlying record for this kind of relation."""
        # pylint: disable=unused-argument
        relation_model = self.env["res.partner.relation"]
        return relation_model.create(vals)

    # pylint: disable=method-required-super
    @api.model_create_multi
    def create(self, vals_list):
        """Divert non-problematic creates to underlying table.

        Create underlying records but return an recordlist of this model.
        """
        result = self.browse([])
        for vals in vals_list:
            type_selection = self._get_type_selection_from_vals(vals)
            if not type_selection:  # Should not happen
                raise ValidationError(
                    _("No relation type specified in vals: %s.") % vals
                )
            vals = self._correct_vals(vals, type_selection)
            base_resource = self.create_resource(vals, type_selection)
            res_id = self._compute_id(base_resource, type_selection)
            result = result | self.browse(res_id)
        return result

    @api.multi
    def unlink_resource(self, base_resource):
        """Delegate unlink to underlying model."""
        self.ensure_one()
        # unlink for models other then res.partner.relation SHOULD
        # be handled in inherited models:
        relation_model = self.env["res.partner.relation"]
        assert self.res_model == relation_model._name
        base_resource.unlink()

    # pylint: disable=method-required-super
    @api.multi
    def unlink(self):
        """For model 'res.partner.relation' call unlink on underlying model."""
        for rec in self:
            try:
                base_resource = rec.get_base_resource()
            except MissingError:
                continue
            rec.unlink_resource(base_resource)
        return True
