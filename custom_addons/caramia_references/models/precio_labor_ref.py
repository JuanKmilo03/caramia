from odoo import models, fields, api

class LaborReferencia(models.Model):
    _name = 'cara.mia.precio.labor.ref'
    _description = 'Labores de Producción y Destajo'

    referencia_id = fields.Many2one('cara.mia.referencia', string='Referencia', required=True, ondelete='cascade')
    
    tipo_labor_id = fields.Many2one(
        'cara.mia.tipo.labor', 
        string='Labor', 
        required=True,
        context={'create': True}
    )
    
    tarifa_pago = fields.Monetary(string='Precio por Par', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id) 

    @api.onchange('tipo_labor_id')
    def _onchange_tipo_labor_id(self):
        for rec in self:
            if rec.tipo_labor_id and rec.referencia_id:
                tarifa_header = rec.referencia_id.tipo_tarifa_header
                if tarifa_header == '2':
                    rec.tarifa_pago = rec.tipo_labor_id.tarifa_especial or 0.0
                elif tarifa_header == '1':
                    rec.tarifa_pago = rec.tipo_labor_id.tarifa_normal or 0.0
            elif not rec.tipo_labor_id:
                rec.tarifa_pago = 0.0