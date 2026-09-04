from odoo import models, fields

class InsumoCatalogo(models.Model):
    _name = 'cara.mia.insumo.catalogo'
    _description = 'Insumo de la Ficha Técnica de Calzado'

    referencia_id = fields.Many2one('cara.mia.referencia', string='Referencia de Calzado', required=True, ondelete='cascade')
    tipo_componente = fields.Selection([
        ('sintetico', 'Material Sintético / Base'),
        ('forro', 'Forro'),
        ('suela', 'Suela'),
        ('horma', 'Horma'),
        ('plantilla', 'Plantilla'),
        ('herraje', 'Herraje / Accesorio'),
        ('otro', 'Otro Insumo')
    ], string='Tipo de Componente', required=True)
    
    name = fields.Char(string='Descripción del Material / Insumo', required=True)
    cantidad = fields.Float(string='Cantidad Requerida', default=1.0)
    unidad_medida = fields.Selection([
        ('cm', 'Cm'),
        ('mts', 'Mts'),
        ('pares', 'Pares'),
        ('und', 'Unidad'),
    ])
    costo_referencia = fields.Monetary(string='Costo Referencia (COP)', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)