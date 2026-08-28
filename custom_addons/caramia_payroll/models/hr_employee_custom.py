from odoo import models, fields

class HrEmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    role_factory = fields.Selection([
        ('guarnecedor', 'Guarnecedor'),
        ('solador', 'Solador / Montador'),
        ('limpiador', 'Limpiador / Empacador'),
    ], string='Labor en Fábrica')
    price_per_pair = fields.Float(string='Precio por Par Fabricado ($)')
