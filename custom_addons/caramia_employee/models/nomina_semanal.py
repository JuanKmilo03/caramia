from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CaramiaNominaSemanal(models.Model):
    _name = 'cara.mia.nomina.semanal'
    _description = 'Nómina Semanal'

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')
    empleado_id = fields.Many2one('cara.mia.empleado', string='Empleado', required=True)
    fecha_inicio = fields.Date(string='Fecha Inicio', required=True, default=fields.Date.context_today)
    fecha_fin = fields.Date(string='Fecha Fin', required=True, default=fields.Date.context_today)
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    # Trae automáticamente los registros de trabajo pendientes del empleado
    registro_trabajo_orden_ids = fields.Many2many(
        'cara.mia.registro.trabajo.orden',
        string='Trabajos a Liquidar',
        compute='_compute_registro_trabajo_orden_ids',
        store=True,
        readonly=False
    )
    
    total_a_pagar = fields.Monetary(
        string='Total a Pagar', 
        compute='_compute_total_a_pagar', 
        store=True, 
        currency_field='currency_id'
    )
    
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('pagado', 'Pagado')
    ], string='Estado', default='borrador', required=True)

    @api.depends('empleado_id', 'fecha_inicio', 'fecha_fin')
    def _compute_registro_trabajo_orden_ids(self):
        for rec in self:
            if rec.empleado_id and rec.fecha_inicio and rec.fecha_fin:
                trabajos = self.env['cara.mia.registro.trabajo.orden'].search([
                    ('empleado_id', '=', rec.empleado_id.id),
                    ('fecha', '>=', rec.fecha_inicio),
                    ('fecha', '<=', rec.fecha_fin),
                    ('estado', '=', 'pendiente')
                ])
                rec.registro_trabajo_orden_ids = [(6, 0, trabajos.ids)]
            else:
                rec.registro_trabajo_orden_ids = [(5, 0, 0)]

    @api.depends('registro_trabajo_orden_ids.subtotal')
    def _compute_total_a_pagar(self):
        for rec in self:
            rec.total_a_pagar = sum(rec.registro_trabajo_orden_ids.mapped('subtotal'))

    def action_liquidar_pago(self):
        for rec in self:
            if not rec.registro_trabajo_orden_ids:
                raise ValidationError("No hay registros de trabajo para liquidar.")
            # Cambia el estado en el modelo registro.trabajo a 'pagado'
            rec.registro_trabajo_orden_ids.write({'estado': 'pagado'})
            rec.write({'estado': 'pagado'})