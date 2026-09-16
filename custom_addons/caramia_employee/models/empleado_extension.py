from odoo import models, fields, api

class CaramiaEmpleado(models.Model):
    _inherit = 'cara.mia.empleado'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    # Enlace inverso con el modelo de registros de trabajo
    registro_trabajo_orden_ids = fields.One2many(
        'cara.mia.registro.trabajo.orden', 
        'empleado_id', 
        string='Historial de Trabajos'
    )

    ganancia_pendiente = fields.Monetary(
        string='Por Cobrar (Pendiente)', 
        compute='_compute_ganancias', 
        currency_field='currency_id'
    )
    
    ganancia_historica = fields.Monetary(
        string='Total Pagado (Histórico)', 
        compute='_compute_ganancias', 
        currency_field='currency_id'
    )

    @api.depends('registro_trabajo_orden_ids.subtotal', 'registro_trabajo_orden_ids.estado')
    def _compute_ganancias(self):
        for rec in self:
            pendientes = rec.registro_trabajo_orden_ids.filtered(lambda r: r.estado == 'pendiente')
            pagados = rec.registro_trabajo_orden_ids.filtered(lambda r: r.estado == 'pagado')
            
            rec.ganancia_pendiente = sum(pendientes.mapped('subtotal'))
            rec.ganancia_historica = sum(pagados.mapped('subtotal'))