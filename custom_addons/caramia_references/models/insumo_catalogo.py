from odoo import models, fields, api

class InsumoCatalogo(models.Model):
    _name = 'cara.mia.insumo.catalogo'
    _description = 'Insumo de la Ficha Técnica de Calzado'
    referencia_id = fields.Many2one('cara.mia.referencia', string='Referencia de Calzado', ondelete='cascade')
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
    
                
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                # Elimina espacios en blanco al inicio y al final
                vals['name'] = vals['name'].strip()
        return super().create(vals_list)
    
    _sql_constraints = [
            ('name_uniq', 'UNIQUE(name)', '¡Ya existe un tipo de componente con este nombre!')
        ]