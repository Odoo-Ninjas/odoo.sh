# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    reception_screen_id = fields.Many2one(
        comodel_name="stock.reception.screen", string="Reception Screen", copy=False
    )

    def action_reception_screen_open(self):
        self.ensure_one()
        # Do not allow to process draft or processed pickings
        if self.state != "assigned":
            raise UserError(_("Your transfer has to be ready to receive goods."))
        # Create the reception screen record
        # NOTE: it is difficult to work with a transient model as we have to
        # reference the screen from the picking/move/move_line.
        if not self.reception_screen_id:
            screen_model = self.env["stock.reception.screen"]
            self.reception_screen_id = screen_model.create({"picking_id": self.id})
        # Reset the screen if we are in a final step
        steps = self.reception_screen_id.get_reception_screen_steps()
        current_step = self.reception_screen_id.current_step
        if not steps[current_step].get("next_steps"):
            self.reception_screen_id.button_reset()
        screen_xmlid = "stock_reception_screen.stock_reception_screen_view_form"
        return {
            "type": "ir.actions.act_window",
            "res_model": self.reception_screen_id._name,
            "res_id": self.reception_screen_id.id,
            "views": [[self.env.ref(screen_xmlid).id, "form"]],
            "target": "fullscreen",
            "flags": {
                "withControlPanel": False,
                "form_view_initial_mode": "edit",
                "no_breadcrumbs": True,
            },
        }

    def action_cancel(self):
        # As the moves are posted individually through the reception screen, we
        # have to put them in a backorder to cancel the remaining ones
        for picking in self:
            if picking.picking_type_code == "incoming":
                picking._create_backorder_for_validated_moves()
        return super().action_cancel()

    def _create_backorder_for_validated_moves(self):
        """Put done moves in a backorder."""
        self.ensure_one()
        done_moves = self.move_lines.filtered(lambda m: m.state == "done")
        new_picking = self.copy({"move_lines": [], "backorder_id": self.id})
        # Set move lines after to bypass checks on creation made by
        # the `_set_scheduled_date` method
        new_picking.move_lines = done_moves
        self.message_post(
            body=_(
                'The backorder <a href="#" '
                'data-oe-model="stock.picking" '
                'data-oe-id="%d">%s</a> has been created.'
            )
            % (new_picking.id, new_picking.name)
        )
