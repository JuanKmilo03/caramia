from odoo import models, fields, api

class InsumoCatalogo(models.Model):
    _name = 'cara.mia.insumo.catalogo'
    _description = 'Insumo de la Ficha Técnica de Calzado'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    tipo_componente_id = fields.Many2one(
        'cara.mia.tipo.componente',
        string='Tipo de Componente',
        required=True
    )
    
    name = fields.Char(string='Descripción del Material / Insumo', required=True)
    unidad_medida = fields.Selection([
        ('cm', 'Cm'),
        ('mts', 'Mts'),
        ('pares', 'Pares'),
        ('und', 'Unidad'),
    ])
    costo_referencia = fields.Monetary(string='Costo Referencia (COP)', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    stock_minimo = fields.Float(string='Stock Mínimo', default=0.0, digits=(16, 2), help='Límite para alertas de escasez')
    entrada_ids = fields.One2many('cara.mia.stock.entrada', 'insumo_id', string='Historial de Entradas')
    stock_actual = fields.Float(string='Stock Actual', compute='_compute_stock_actual', store=True, digits=(16, 2))
      
    @api.depends('entrada_ids.cantidad')
    def _compute_stock_actual(self):
        for record in self:
            calculo = sum(record.entrada_ids.mapped('cantidad'))
            record.stock_actual = max(0.0, calculo)