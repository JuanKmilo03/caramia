from odoo import models, fields, api

class CaramiaWorkLog(models.Model):
    _name = 'caramia.work.log'
    _description = 'Registro de Trabajo Diario / Destajo'

    paysheet_id = fields.Many2one('caramia.weekly.paysheet', string='Liquidación Semanal', ondelete='cascade')
    employee_id = fields.Many2one(related='paysheet_id.employee_id', string='Empleado', store=True)
    labor_activity_id = fields.Many2one(
        'caramia.production.labor', string='Actividad de producción',
        ondelete='set null', copy=False, readonly=True,
    )
    production_id = fields.Many2one(
        related='labor_activity_id.production_id', string='Orden de producción', store=True, readonly=True
    )
    date = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    pairs_qty = fields.Integer(string='Cantidad de Pares', default=0, required=True)
    price_per_pair = fields.Monetary(string='Precio por par', required=True, default=0.0)
    extra_amount = fields.Monetary(string='Extras', default=0.0)
    extra_note = fields.Char(string='Detalle de extras')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one(related='paysheet_id.currency_id', store=True, readonly=True)

    @api.depends('pairs_qty', 'price_per_pair', 'extra_amount')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = (record.pairs_qty * record.price_per_pair) + record.extra_amount

    _sql_constraints = [
        ('caramia_work_log_activity_uniq', 'unique(labor_activity_id)',
         'Una actividad de producción solo puede estar en una liquidación.'),
        ('caramia_work_log_pairs_positive', 'CHECK(pairs_qty >= 0)',
         'La cantidad de pares no puede ser negativa.'),
    ]
