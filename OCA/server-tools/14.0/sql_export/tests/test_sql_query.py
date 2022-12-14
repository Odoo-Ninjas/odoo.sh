# Copyright (C) 2015 Akretion (<http://www.akretion.com>)
# @author: Florian da Costa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import config


@tagged("post_install", "-at_install")
class TestExportSqlQuery(TransactionCase):
    def setUp(self):
        super(TestExportSqlQuery, self).setUp()
        self.sql_export_obj = self.env["sql.export"]
        self.wizard_obj = self.env["sql.file.wizard"]
        self.sql_report_demo = self.env.ref("sql_export.sql_export_partner")

    def test_sql_query(self):
        wizard = self.wizard_obj.create(
            {
                "sql_export_id": self.sql_report_demo.id,
            }
        )
        wizard.export_sql()
        export = base64.b64decode(wizard.binary_file).decode("utf-8")
        self.assertEqual(export.split(";")[0], "name")
        self.assertTrue(len(export.split(";")) > 6)

    def test_prohibited_queries(self):
        prohibited_queries = [
            "upDaTe res_partner SET name = 'test' WHERE id = 1",
            "DELETE FROM sql_export WHERE name = 'test';",
            "  DELETE FROM sql_export WHERE name = 'test'   ;",
            """DELETE
            FROM
            sql_export
            WHERE name = 'test'
            """,
        ]
        for query in prohibited_queries:
            with self.assertRaises(UserError):
                sql_export = self.sql_export_obj.create(
                    {"name": "test_prohibited", "query": query}
                )
                sql_export.button_validate_sql_expression()

    def test_authorized_queries(self):
        authorized_queries = [
            "SELECT create_date FROM res_partner",
        ]

        for query in authorized_queries:
            sql_export = self.sql_export_obj.create(
                {"name": "test_authorized", "query": query}
            )
            sql_export.button_validate_sql_expression()
            self.assertEqual(
                sql_export.state, "sql_valid", "%s is a valid request" % (query)
            )

    def test_sql_query_with_params(self):
        query = self.env.ref("sql_export.sql_export_partner_with_variables")
        categ_id = self.env.ref("base.res_partner_category_0").id
        wizard = self.wizard_obj.create(
            {
                "sql_export_id": query.id,
                "x_date": fields.Date.today(),
                "x_id": 1,
                "x_partner_categ_ids": [(6, 0, [categ_id])],
            }
        )
        wizard.export_sql()
        export = base64.b64decode(wizard.binary_file)
        self.assertTrue(export)

    def test_sql_query_external_database(self):
        # since we can't easily test a query on an external database
        # without mock, we just test that, when the option is checked, the
        # query is executed on a different cursor. Meaning Odoo did
        # successfully opened a new database connection.
        self.sql_report_demo = self.env.ref("sql_export.sql_export_partner")
        res_sql = self.sql_report_demo._execute_sql_request(mode="fetchall")
        partner_count = len(res_sql)

        self.env["res.partner"].create({"name": "test"})
        res_sql = self.sql_report_demo._execute_sql_request(mode="fetchall")
        # The partner created on original cursor is present in the new result
        # of the query
        self.assertEqual(len(res_sql), partner_count + 1)

        config["external_db_name"] = self.env.cr.dbname
        self.sql_report_demo.write({"use_external_database": True})
        res_sql = self.sql_report_demo._execute_sql_request(mode="fetchall")
        # The partner created in original cursor is not present because
        # a new cursor has been opened.
        self.assertEqual(len(res_sql), partner_count)
