# See LICENSE file for full copyright and licensing details.

import time

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class HotelFolio(models.Model):

    _inherit = "hotel.folio"

    hotel_reservation_order_ids = fields.Many2many(
        "hotel.reservation.order",
        "hotel_res_rel",
        "hotel_folio_id",
        "reste_id",
        "Orders",
    )
    hotel_restaurant_order_ids = fields.Many2many(
        "hotel.restaurant.order",
        "hotel_res_resv",
        "hfolio_id",
        "reserves_id",
        "Orders",
    )


class HotelMenucardType(models.Model):

    _name = "hotel.menucard.type"
    _description = "Food Item Type"

    name = fields.Char("Name", required=True)
    menu_id = fields.Many2one("hotel.menucard.type", string="Food Item Type")
    child_ids = fields.One2many(
        "hotel.menucard.type", "menu_id", "Child Categories"
    )

    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.menu_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.menu_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        if not args:
            args = []
        if name:
            # Be sure name_search is symetric to name_get
            category_names = name.split(" / ")
            parents = list(category_names)
            child = parents.pop()
            domain = [("name", operator, child)]
            if parents:
                names_ids = self.name_search(
                    " / ".join(parents),
                    args=args,
                    operator="ilike",
                    limit=limit,
                )
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    categories = self.search([("id", "not in", category_ids)])
                    domain = expression.OR(
                        [[("menu_id", "in", categories.ids)], domain]
                    )
                else:
                    domain = expression.AND(
                        [[("menu_id", "in", category_ids)], domain]
                    )
                for i in range(1, len(category_names)):
                    domain = [
                        [
                            (
                                "name",
                                operator,
                                " / ".join(category_names[-1 - i :]),
                            )
                        ],
                        domain,
                    ]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            categories = self.search(
                expression.AND([domain, args]), limit=limit
            )
        else:
            categories = self.search(args, limit=limit)
        return categories.name_get()


class HotelMenucard(models.Model):

    _name = "hotel.menucard"
    _description = "Hotel Menucard"

    product_id = fields.Many2one(
        "product.product",
        "Product",
        required=True,
        delegate=True,
        ondelete="cascade",
        index=True,
    )
    categ_id = fields.Many2one(
        "hotel.menucard.type", string="Food Item Category", required=True
    )
    image = fields.Binary(
        "Image",
        help="This field holds the image used as image "
        "for the product, limited to 1024x1024px.",
    )
    product_manager = fields.Many2one("res.users", string="Product Manager")


class HotelRestaurantTables(models.Model):

    _name = "hotel.restaurant.tables"
    _description = "Includes Hotel Restaurant Table"

    name = fields.Char("Table Number", required=True, index=True)
    capacity = fields.Integer("Capacity")


class HotelRestaurantReservation(models.Model):
    @api.multi
    def create_order(self):
        """
        This method is for create a new order for hotel restaurant
        reservation .when table is booked and create order button is
        clicked then this method is called and order is created.you
        can see this created order in "Orders"
        ------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel restaurant reservation.
        """
        reservation_order = self.env["hotel.reservation.order"]
        for record in self:
            table_ids = [tableno.id for tableno in record.tableno]
            values = {
                "reservationno": record.id,
                "order_date": record.start_date,
                "folio_id": record.folio_id.id,
                "table_no": [(6, 0, table_ids)],
                "is_folio": record.is_folio,
            }
            reservation_order.create(values)
        self.write({"state": "order"})
        return True

    @api.onchange("cname")
    def onchange_partner_id(self):
        """
        When Customer name is changed respective adress will display
        in Adress field
        @param self: object pointer
        """
        if not self.cname:
            self.partner_address_id = False
        else:
            addr = self.cname.address_get(["default"])
            self.partner_address_id = addr["default"]

    @api.onchange("folio_id")
    def get_folio_id(self):
        """
        When you change folio_id, based on that it will update
        the cname and room_number as well
        ---------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.cname = False
            rec.room_no = False
            if rec.folio_id:
                rec.cname = rec.folio_id.partner_id.id
                if rec.folio_id.room_lines:
                    rec.room_no = rec.folio_id.room_lines[0].product_id.id

    @api.multi
    def action_set_to_draft(self):
        """
        This method is used to change the state
        to draft of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        self.state = "draft"
        return True

    @api.multi
    def table_reserved(self):
        """
        when CONFIRM BUTTON is clicked this method is called for
        table reservation
        @param self: The object pointer
        @return: change a state depending on the condition
        """
        for reservation in self:
            self._cr.execute(
                "select count(*) from "
                "hotel_restaurant_reservation as hrr "
                "inner join reservation_table as rt on \
                             rt.reservation_table_id = hrr.id "
                "where (start_date,end_date)overlaps\
                             ( timestamp %s , timestamp %s ) "
                "and hrr.id<> %s and state != 'done'"
                "and rt.name in (select rt.name from \
                             hotel_restaurant_reservation as hrr "
                "inner join reservation_table as rt on \
                             rt.reservation_table_id = hrr.id "
                "where hrr.id= %s) ",
                (
                    reservation.start_date,
                    reservation.end_date,
                    reservation.id,
                    reservation.id,
                ),
            )
            res = self._cr.fetchone()
            roomcount = res and res[0] or 0.0
            if len(reservation.tableno.ids) == 0:
                raise ValidationError(
                    _(
                        "Please Select Tables For \
                                         Reservation"
                    )
                )
            if roomcount:
                raise ValidationError(
                    _(
                        "You tried to confirm reservation \
                                         with table those already reserved \
                                         in this reservation period"
                    )
                )
            self.state = "confirm"
            return True

    @api.multi
    def table_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        self.state = "cancel"
        return True

    @api.multi
    def table_done(self):
        """
        This method is used to change the state
        to done of the hotel restaurant reservation
        --------------------------------------------
        @param self: object pointer
        """
        self.state = "done"
        return True

    _name = "hotel.restaurant.reservation"
    _description = "Includes Hotel Restaurant Reservation"
    _rec_name = "reservation_id"

    reservation_id = fields.Char("Reservation No", readonly=True, index=True)
    room_no = fields.Many2one("product.product", string="Room No", index=True)
    folio_id = fields.Many2one("hotel.folio", string="Folio No")
    start_date = fields.Datetime(
        "Start Time",
        required=True,
        default=(lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
    )
    end_date = fields.Datetime("End Time", required=True)
    cname = fields.Many2one(
        "res.partner", string="Customer Name", required=True, index=True
    )
    partner_address_id = fields.Many2one("res.partner", string="Address")
    tableno = fields.Many2many(
        "hotel.restaurant.tables",
        relation="reservation_table",
        index=True,
        column1="reservation_table_id",
        column2="name",
        string="Table Number",
        help="Table reservation detail. ",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("order", "Order Created"),
        ],
        "state",
        index=True,
        required=True,
        readonly=True,
        default=lambda *a: "draft",
    )
    is_folio = fields.Boolean("Is a Hotel Guest??")

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        seq_obj = self.env["ir.sequence"]
        resrve = seq_obj.next_by_code("hotel.restaurant.reservation") or "New"
        vals["reservation_id"] = resrve
        return super(HotelRestaurantReservation, self).create(vals)

    @api.constrains("start_date", "end_date")
    def check_start_dates(self):
        """
        This method is used to validate the start_date and end_date.
        -------------------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        """
        if self.start_date >= self.end_date:
            raise ValidationError(
                _(
                    "Start Date Should be less \
            than the End Date!"
                )
            )
        if self.is_folio is True:
            if self.start_date < self.folio_id.room_lines.checkin_date:
                raise ValidationError(
                    _(
                        "Start Date Should be greater than the"
                        " Folio Check-in Date!"
                    )
                )
            if self.end_date > self.folio_id.room_lines.checkout_date:
                raise ValidationError(
                    _(
                        "End Date Should be less than the"
                        " Folio Check-out Date!"
                    )
                )


class HotelRestaurantKitchenOrderTickets(models.Model):

    _name = "hotel.restaurant.kitchen.order.tickets"
    _description = "Includes Hotel Restaurant Order"
    _rec_name = "orderno"

    orderno = fields.Char("Order Number", readonly=True)
    resno = fields.Char("Reservation Number")
    kot_date = fields.Datetime("Date")
    room_no = fields.Char("Room No", readonly=True)
    w_name = fields.Char("Waiter Name", readonly=True)
    tableno = fields.Many2many(
        "hotel.restaurant.tables",
        "temp_table3",
        "table_no",
        "name",
        "Table Number",
        help="Table reservation detail.",
    )
    kot_list = fields.One2many(
        "hotel.restaurant.order.list",
        "kot_order_list",
        "Order List",
        help="Kitchen order list",
    )


class HotelRestaurantOrder(models.Model):
    @api.multi
    @api.depends("order_list")
    def _compute_amount_all_total(self):
        """
        amount_subtotal and amount_total will display on change of order_list
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        for sale in self:
            sale.amount_subtotal = sum(
                line.price_subtotal for line in sale.order_list
            )
            if sale.amount_subtotal:
                sale.amount_total = (
                    sale.amount_subtotal
                    + (sale.amount_subtotal * sale.tax) / 100
                )

    @api.onchange("folio_id")
    def get_folio_id(self):
        """
        When you change folio_id, based on that it will update
        the cname and room_number as well
        ---------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            self.cname = False
            self.room_no = False
            if rec.folio_id:
                self.cname = rec.folio_id.partner_id.id
                if rec.folio_id.room_lines:
                    self.room_no = rec.folio_id.room_lines[0].product_id.id

    @api.multi
    def done_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        self.state = "cancel"
        return True

    @api.multi
    def set_to_draft(self):
        """
        This method is used to change the state
        to draft of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        self.state = "draft"
        return True

    @api.multi
    def generate_kot(self):
        """
        This method create new record for hotel restaurant order list.
        @param self: The object pointer
        @return: new record set for hotel restaurant order list.
        """
        res = []
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        restaurant_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            if len(order.order_list.ids) == 0:
                raise ValidationError(_("Please Give an Order"))
            if len(order.table_no.ids) == 0:
                raise ValidationError(_("Please Assign a Table"))
            table_ids = [x.id for x in order.table_no]
            kot_data = order_tickets_obj.create(
                {
                    "orderno": order.order_no,
                    "kot_date": order.o_date,
                    "room_no": order.room_no.name,
                    "w_name": order.waiter_name.name,
                    "tableno": [(6, 0, table_ids)],
                }
            )
            self.kitchen_id = kot_data.id
            for order_line in order.order_list:
                o_line = {
                    "kot_order_list": kot_data.id,
                    "name": order_line.name.id,
                    "item_qty": order_line.item_qty,
                    "item_rate": order_line.item_rate,
                }
                restaurant_order_list_obj.create(o_line)
                res.append(order_line.id)
            self.rest_item_id = [(6, 0, res)]
            self.state = "order"
        return True

    _name = "hotel.restaurant.order"
    _description = "Includes Hotel Restaurant Order"
    _rec_name = "order_no"

    order_no = fields.Char("Order Number", readonly=True)
    o_date = fields.Datetime(
        "Order Date",
        required=True,
        default=(lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
    )
    room_no = fields.Many2one("product.product", string="Room No")
    folio_id = fields.Many2one("hotel.folio", string="Folio No")
    waiter_name = fields.Many2one("res.partner", "Waiter Name")
    table_no = fields.Many2many(
        "hotel.restaurant.tables",
        "temp_table2",
        "table_no",
        "name",
        "Table Number",
    )
    order_list = fields.One2many(
        "hotel.restaurant.order.list", "o_list", "Order List"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", method=True, string="Subtotal"
    )
    amount_total = fields.Float(
        compute="_compute_amount_all_total", method=True, string="Total"
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("order", "Order Created"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        "State",
        index=True,
        required=True,
        readonly=True,
        default=lambda *a: "draft",
    )
    is_folio = fields.Boolean(
        "Is a Hotel Guest??", help="is customer reside" "in hotel or not"
    )
    cname = fields.Many2one(
        "res.partner", string="Customer Name", required=True
    )
    kitchen_id = fields.Integer("Kitchen id")
    rest_item_id = fields.Many2many(
        "hotel.restaurant.order.list",
        "restau_kitc_ids",
        "restau_id",
        "kit_id",
        "Rest",
    )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        seq_obj = self.env["ir.sequence"]
        rest_order = seq_obj.next_by_code("hotel.restaurant.order") or "New"
        vals["order_no"] = rest_order
        return super(HotelRestaurantOrder, self).create(vals)

    @api.multi
    def generate_kot_update(self):
        """
        This method update record for hotel restaurant order list.
        ----------------------------------------------------------
        @param self: The object pointer
        @return: update record set for hotel restaurant order list.
        """
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            table_ids = order.table_no.ids
            line_data = {
                "orderno": order.order_no,
                "kot_date": time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "room_no": order.room_no.name,
                "w_name": order.waiter_name.name,
                "tableno": [(6, 0, table_ids)],
            }
            kot_rec = order_tickets_obj.browse(self.kitchen_id)
            kot_rec.write(line_data)
            for order_line in order.order_list:
                if order_line.id not in order.rest_item_id.ids:
                    kot_data1 = order_tickets_obj.create(line_data)
                    order.kitchen_id = kot_data1.id
                    o_line = {
                        "kot_order_list": kot_data1.id,
                        "name": order_line.name.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    order.rest_item_id = [(4, order_line.id)]
                    rest_order_list_obj.create(o_line)
        return True

    @api.multi
    def done_order_kot(self):
        """
        This method is used to change the state
        to done of the hotel restaurant order
        ----------------------------------------
        @param self: object pointer
        """
        hotel_folio_obj = self.env["hotel.folio"]
        hsl_obj = self.env["hotel.service.line"]
        so_line_obj = self.env["sale.order.line"]
        for order_obj in self:
            hotelfolio = order_obj.folio_id.order_id.id
            if order_obj.folio_id:
                for order in order_obj.order_list:
                    values = {
                        "order_id": hotelfolio,
                        "name": order.name.name,
                        "product_id": order.name.product_id.id,
                        "product_uom": order.name.uom_id.id,
                        "product_uom_qty": order.item_qty,
                        "price_unit": order.item_rate,
                        "price_subtotal": order.price_subtotal,
                    }
                    sol_rec = so_line_obj.create(values)
                    hsl_obj.create(
                        {
                            "folio_id": order_obj.folio_id.id,
                            "service_line_id": sol_rec.id,
                        }
                    )
                    hf_rec = hotel_folio_obj.browse(order_obj.folio_id.id)
                    hf_rec.write(
                        {"hotel_restaurant_order_ids": [(4, order_obj.id)]}
                    )
            self.state = "done"
        return True


class HotelReservationOrder(models.Model):
    @api.multi
    @api.depends("order_list")
    def _compute_amount_all_total(self):
        """
        amount_subtotal and amount_total will display on change of order_list
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        for sale in self:
            sale.amount_subtotal = sum(
                line.price_subtotal for line in sale.order_list
            )
            if sale.amount_subtotal:
                sale.amount_total = (
                    sale.amount_subtotal
                    + (sale.amount_subtotal * sale.tax) / 100.0
                )

    @api.multi
    def reservation_generate_kot(self):
        """
        This method create new record for hotel restaurant order list.
        --------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel restaurant order list.
        """
        res = []
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            if len(order.order_list) == 0:
                raise ValidationError(_("Please Give an Order"))
            table_ids = [x.id for x in order.table_no]
            line_data = {
                "orderno": order.order_number,
                "resno": order.reservationno.reservation_id,
                "kot_date": order.order_date,
                "w_name": order.waitername.name,
                "tableno": [(6, 0, table_ids)],
            }
            kot_data = order_tickets_obj.create(line_data)
            self.kitchen_id = kot_data.id
            for order_line in order.order_list:
                o_line = {
                    "kot_order_list": kot_data.id,
                    "name": order_line.name.id,
                    "item_qty": order_line.item_qty,
                    "item_rate": order_line.item_rate,
                }
                rest_order_list_obj.create(o_line)
                res.append(order_line.id)
            self.rest_id = [(6, 0, res)]
            self.state = "order"
        return res

    @api.multi
    def reservation_update_kot(self):
        """
        This method update record for hotel restaurant order list.
        ----------------------------------------------------------
        @param self: The object pointer
        @return: update record set for hotel restaurant order list.
        """
        order_tickets_obj = self.env["hotel.restaurant.kitchen.order.tickets"]
        rest_order_list_obj = self.env["hotel.restaurant.order.list"]
        for order in self:
            table_ids = [x.id for x in order.table_no]
            line_data = {
                "orderno": order.order_number,
                "resno": order.reservationno.reservation_id,
                "kot_date": time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "w_name": order.waitername.name,
                "tableno": [(6, 0, table_ids)],
            }
            kot_rec = order_tickets_obj.browse(self.kitchen_id)
            kot_rec.write(line_data)
            for order_line in order.order_list:

                if order_line not in order.rest_id.ids:
                    kot_data1 = order_tickets_obj.create(line_data)
                    order.kitchen_id = kot_data1.id
                    o_line = {
                        "kot_order_list": kot_data1.id,
                        "name": order_line.name.id,
                        "item_qty": order_line.item_qty,
                        "item_rate": order_line.item_rate,
                    }
                    self.rest_id = [(4, order_line.id)]
                    rest_order_list_obj.create(o_line)
        return True

    @api.multi
    def done_kot(self):
        """
        This method is used to change the state
        to done of the hotel reservation order
        ----------------------------------------
        @param self: object pointer
        """
        hotel_folio_obj = self.env["hotel.folio"]
        hsl_obj = self.env["hotel.service.line"]
        so_line_obj = self.env["sale.order.line"]
        for order_obj in self:
            hotelfolio = order_obj.folio_id.order_id.id
            if order_obj.folio_id:

                for order in order_obj.order_list:
                    values = {
                        "order_id": hotelfolio,
                        "name": order.name.name,
                        "product_id": order.name.product_id.id,
                        "product_uom_qty": order.item_qty,
                        "price_unit": order.item_rate,
                        "price_subtotal": order.price_subtotal,
                    }
                    sol_rec = so_line_obj.create(values)
                    hsl_obj.create(
                        {
                            "folio_id": order_obj.folio_id.id,
                            "service_line_id": sol_rec.id,
                        }
                    )
                    hf_rec = hotel_folio_obj.browse(order_obj.folio_id.id)
                    hf_rec.write(
                        {"hotel_reservation_order_ids": [(4, order_obj.id)]}
                    )
            if order_obj.reservationno:
                order_obj.reservationno.write({"state": "done"})
        self.state = "done"
        return True

    _name = "hotel.reservation.order"
    _description = "Reservation Order"
    _rec_name = "order_number"

    order_number = fields.Char("Order No", readonly=True)
    reservationno = fields.Many2one(
        "hotel.restaurant.reservation", "Reservation No"
    )
    order_date = fields.Datetime(
        "Date",
        required=True,
        default=(lambda *a: time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
    )
    waitername = fields.Many2one("res.partner", "Waiter Name")
    table_no = fields.Many2many(
        "hotel.restaurant.tables",
        "temp_table4",
        "table_no",
        "name",
        "Table Number",
    )
    order_list = fields.One2many(
        "hotel.restaurant.order.list", "o_l", "Order List"
    )
    tax = fields.Float("Tax (%) ")
    amount_subtotal = fields.Float(
        compute="_compute_amount_all_total", method=True, string="Subtotal"
    )
    amount_total = fields.Float(
        compute="_compute_amount_all_total", method=True, string="Total"
    )
    kitchen_id = fields.Integer("Kitchen id")
    rest_id = fields.Many2many(
        "hotel.restaurant.order.list",
        "reserv_id",
        "kitchen_id",
        "res_kit_ids",
        "Rest",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("order", "Order Created"), ("done", "Done")],
        "State",
        index=True,
        required=True,
        readonly=True,
        default=lambda *a: "draft",
    )
    folio_id = fields.Many2one("hotel.folio", string="Folio No")
    is_folio = fields.Boolean(
        "Is a Hotel Guest??", help="is customer reside" "in hotel or not"
    )

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        seq_obj = self.env["ir.sequence"]
        res_oder = seq_obj.next_by_code("hotel.reservation.order") or "New"
        vals["order_number"] = res_oder
        return super(HotelReservationOrder, self).create(vals)


class HotelRestaurantOrderList(models.Model):
    @api.multi
    @api.depends("item_qty", "item_rate")
    def _compute_price_subtotal(self):
        """
        price_subtotal will display on change of item_rate
        --------------------------------------------------
        @param self: object pointer
        """
        for line in self:
            line.price_subtotal = line.item_rate * int(line.item_qty)

    @api.onchange("name")
    def on_change_item_name(self):
        """
        item rate will display on change of item name
        ---------------------------------------------
        @param self: object pointer
        """
        if self.name:
            self.item_rate = self.name.list_price

    _name = "hotel.restaurant.order.list"
    _description = "Includes Hotel Restaurant Order"

    o_list = fields.Many2one("hotel.restaurant.order", "Restaurant Order")
    o_l = fields.Many2one("hotel.reservation.order", "Reservation Order")
    kot_order_list = fields.Many2one(
        "hotel.restaurant.kitchen.order.tickets", "Kitchen Order Tickets"
    )
    name = fields.Many2one("hotel.menucard", "Item Name", required=True)
    item_qty = fields.Integer("Qty", required=True, default=1)
    item_rate = fields.Float("Rate")
    price_subtotal = fields.Float(
        compute="_compute_price_subtotal", method=True, string="Subtotal"
    )
