from odoo import models, fields

class MrpProductionCustom(models.Model):
    _inherit = 'mrp.production'

    shoe_reference_id = fields.Many2one('caramia.shoe.reference', string='Referencia de Calzado')
    barcode_labor = fields.Char(string='Código de Barras para Escaneo de Labor')
    pairs_count = fields.Integer(string='Total Pares a Fabricar', default=12)
