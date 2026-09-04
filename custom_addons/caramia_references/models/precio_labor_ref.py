from odoo import models, fields

class LaborReferencia(models.Model):
    _name = 'cara.mia.precio.labor.ref'
    _description = 'Labores de Producción y Destajo'

    referencia_id = fields.Many2one('cara.mia.referencia', string='Referencia de Calzado', required=True, ondelete='cascade')
    tipo_labor = fields.Selection([
        ('corte', 'Corte'),
        ('guarnicion', 'Guarnición'),
        ('montada', 'Montada'),
        ('limpiada', 'Limpiada'),
        ('forrada', 'Forrada'),
        ('plantilla', 'Plantilla'),
        ('otro', 'Otra Labor')
    ], string='Tipo de Labor', required=True)
    
    tarifa_pago = fields.Monetary(string='Precio por Par', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)