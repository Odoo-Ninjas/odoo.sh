# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
{
    "name": "Stock reception screen qty by packaging",
    "summary": "Glue module for `stock_product_qty_by_packaging` and `stock_vertical_lift`.",
    "version": "14.0.1.1.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": True,
    "depends": ["stock_product_qty_by_packaging", "stock_reception_screen"],
    "data": ["views/stock_reception_screen.xml"],
}
