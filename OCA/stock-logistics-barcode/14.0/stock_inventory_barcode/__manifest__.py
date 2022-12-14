# Copyright 2015-2021 Akretion France (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Barcode Input for Inventories",
    "version": "14.0.1.0.0",
    "category": "Inventory, Logistic, Storage",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "summary": "Add simple barcode interface on inventories",
    "website": "https://github.com/OCA/stock-logistics-barcode",
    "license": "AGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/stock_inventory_barcode_view.xml",
        "views/stock_inventory.xml",
    ],
    "installable": True,
}
