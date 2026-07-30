from odoo import models, fields

class ShoeReference(models.Model):
    _name = 'caramia.shoe.reference'
    _description = 'Ficha Técnica y Referencia de Calzado'

    code = fields.Char(string='Código de Referencia', required=True)
    name = fields.Char(string='Nombre del Modelo', required=True)
    image = fields.Binary(string='Imagen del Calzado')
    description = fields.Text(string='Descripción')
    material_line_ids = fields.One2many('caramia.shoe.material.line', 'reference_id', string='Insumos')

class ShoeMaterialLine(models.Model):
    _name = 'caramia.shoe.material.line'
    _description = 'Línea de Materiales e Insumos'

    reference_id = fields.Many2one('caramia.shoe.reference', string='Referencia')
    product_id = fields.Many2one('product.product', string='Insumo (Suela, Horma, Sintético)', required=True)
    quantity = fields.Float(string='Cantidad Requerida', default=1.0)
