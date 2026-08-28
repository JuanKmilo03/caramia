from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MrpProductionLabor(models.Model):
    _inherit = 'mrp.production'

    labor_activity_ids = fields.One2many(
        'caramia.production.labor', 'production_id', string='Actividades de mano de obra'
    )


class CaramiaProductionLabor(models.Model):
    _name = 'caramia.production.labor'
    _description = 'Actividad de mano de obra'
    _order = 'work_date desc, id desc'

    production_id = fields.Many2one(
        'mrp.production', string='Orden de producción', required=True, ondelete='cascade', index=True
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Empleado', required=True, index=True,
        domain="[('active', '=', True)]",
    )
    role_id = fields.Many2one(
        'caramia.employee.role', string='Rol aplicado', required=True,
        domain="[('active', '=', True)]",
    )
    work_date = fields.Date(string='Fecha de entrega', default=fields.Date.context_today, required=True)
    pairs_qty = fields.Integer(string='Pares entregados', required=True, default=0)
    price_per_pair = fields.Monetary(string='Precio por par aplicado', required=True, default=0.0)
    extra_amount = fields.Monetary(string='Extras', default=0.0)
    extra_note = fields.Char(string='Detalle de extras')
    amount_total = fields.Monetary(string='Valor de la actividad', compute='_compute_amount_total', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', default=lambda self: self.env.company.currency_id, required=True
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('delivered', 'Entregada'),
        ('settled', 'Liquidada'),
    ], string='Estado', default='draft', required=True, copy=False)
    notes = fields.Text(string='Observaciones')

    @api.depends('pairs_qty', 'price_per_pair', 'extra_amount')
    def _compute_amount_total(self):
        for activity in self:
            activity.amount_total = (activity.pairs_qty * activity.price_per_pair) + activity.extra_amount

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id.factory_role_id:
            self.role_id = self.employee_id.factory_role_id
            self.price_per_pair = self.role_id.price_per_pair

    @api.onchange('role_id')
    def _onchange_role_id(self):
        if self.role_id:
            self.price_per_pair = self.role_id.price_per_pair

    @api.constrains('pairs_qty', 'price_per_pair', 'extra_amount')
    def _check_non_negative_values(self):
        for activity in self:
            if activity.pairs_qty < 0 or activity.price_per_pair < 0 or activity.extra_amount < 0:
                raise ValidationError('Los pares, la tarifa y los extras no pueden ser negativos.')

    def action_mark_delivered(self):
        self.filtered(lambda activity: activity.state == 'draft').write({'state': 'delivered'})

    def action_reset_draft(self):
        self.filtered(lambda activity: activity.state == 'delivered').write({'state': 'draft'})
