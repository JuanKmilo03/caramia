from odoo import models, fields

class CaramiaCostoLaborLine(models.Model):
    _name = 'caramia.costo.labor.line'
    _description = 'Línea de Labor - Hoja de Costos'

    costo_id = fields.Many2one(
        'caramia.costo',
        string='Cotización',
        required=True,
        ondelete='cascade'
    )
    tipo_labor_id = fields.Many2one(
        'cara.mia.tipo.labor',
        string='Tipo de Labor'
    )
    costo_par = fields.Float(
        string='Costo Por Par',
        default=0.0
    )