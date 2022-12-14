# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields


class X2MDemo(models.Model):
    _name = 'x2m.demo'
    _description = 'X2Many Demo'

    name = fields.Char()

    display_name = fields.Char(compute="_compute_display_name")

    line_ids = fields.One2many('x2m.demo.line', 'demo_id')

    @api.depends("name")
    def _compute_display_name(self):
        for demo in self:
            demo.display_name = "%s (#%s)" % (demo.name, demo.id)

    @api.multi
    def _open_x2m_matrix(self, view_xmlid):
        wiz = self.env['x2m.matrix.demo.wiz'].create({})
        view_id = self.env.ref(
            'web_widget_x2many_2d_matrix_example.%s' % view_xmlid,
        ).id
        return {
            'name': 'Try x2many 2D matrix widget',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'x2m.matrix.demo.wiz',
            'target': 'new',
            'res_id': wiz.id,
            'view_id': view_id,
            'context': self.env.context,
        }

    @api.multi
    def open_x2m_matrix(self):
        return self._open_x2m_matrix('x2many_2d_matrix_demo')

    @api.multi
    def open_x2m_matrix_selection(self):
        return self._open_x2m_matrix('x2many_2d_matrix_demo_selection')

    @api.multi
    def open_x2m_matrix_many2one(self):
        return self._open_x2m_matrix('x2many_2d_matrix_demo_many2one')


class X2MDemoLine(models.Model):
    _name = 'x2m.demo.line'
    _description = 'X2Many Demo Line'

    name = fields.Char()
    demo_id = fields.Many2one('x2m.demo')
    demo_display_name = fields.Char(related="demo_id.display_name")
    user_id = fields.Many2one('res.users')
    user_display_name = fields.Char(related="user_id.matrix_display_name")
    value = fields.Integer()
    value_selection = fields.Selection(
        [('val1', 'Value 1'), ('val2', 'Value 2')],
    )
    value_many2one = fields.Many2one('res.groups')
