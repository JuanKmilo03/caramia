from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class CaramiaWeeklyPaysheet(models.Model):
    _name = 'caramia.weekly.paysheet'
    _description = 'Liquidación semanal de nómina'
    _order = 'date_end desc, id desc'

    name = fields.Char(string='Referencia / folio', required=True, copy=False, readonly=True, default='Nuevo')
    employee_id = fields.Many2one(
        'hr.employee', string='Empleado', required=True, domain="[('active', '=', True)]", index=True
    )
    date_start = fields.Date(string='Fecha de inicio', required=True)
    date_end = fields.Date(string='Fecha de fin', required=True)
    work_log_ids = fields.One2many('caramia.work.log', 'paysheet_id', string='Registros de trabajo')
    currency_id = fields.Many2one(
        'res.currency', string='Moneda', default=lambda self: self.env.company.currency_id, required=True
    )
    total_pairs = fields.Integer(string='Total pares', compute='_compute_totals', store=True)
    gross_amount = fields.Monetary(string='Pago por producción y extras', compute='_compute_totals', store=True)
    annual_reserve_rate = fields.Float(
        string='Reserva anual (%)', default=0.22,
        help='Porcentaje aplicado al pago semanal. El valor 0,22 corresponde a 0,22%.',
    )
    annual_reserve_amount = fields.Monetary(
        string='Reserva para liquidación anual', compute='_compute_totals', store=True
    )
    material_damage_discount = fields.Monetary(string='Descuento por daños materiales', default=0.0)
    damage_note = fields.Char(string='Detalle del descuento')
    net_amount = fields.Monetary(string='Neto a pagar', compute='_compute_totals', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('paid', 'Pagado'),
    ], string='Estado', default='draft', required=True, copy=False)

    @api.depends(
        'work_log_ids.pairs_qty', 'work_log_ids.subtotal',
        'annual_reserve_rate', 'material_damage_discount'
    )
    def _compute_totals(self):
        for record in self:
            record.total_pairs = sum(record.work_log_ids.mapped('pairs_qty'))
            record.gross_amount = sum(record.work_log_ids.mapped('subtotal'))
            record.annual_reserve_amount = record.gross_amount * (record.annual_reserve_rate / 100.0)
            record.net_amount = record.gross_amount - record.material_damage_discount

    @api.constrains('date_start', 'date_end', 'annual_reserve_rate', 'material_damage_discount')
    def _check_paysheet_values(self):
        for record in self:
            if record.date_start and record.date_end and record.date_start > record.date_end:
                raise ValidationError('La fecha de inicio no puede ser posterior a la fecha de fin.')
            if record.annual_reserve_rate < 0 or record.material_damage_discount < 0:
                raise ValidationError('La reserva y los descuentos no pueden ser negativos.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('caramia.weekly.paysheet') or 'LIQ-0000'
        return super().create(vals_list)

    def action_load_delivered_activities(self):
        for record in self:
            if record.state != 'draft':
                raise UserError('Solo se pueden cargar actividades en una liquidación en borrador.')
            if not record.employee_id or not record.date_start or not record.date_end:
                raise UserError('Indique empleado y periodo antes de cargar las actividades entregadas.')
            activities = self.env['caramia.production.labor'].search([
                ('employee_id', '=', record.employee_id.id),
                ('work_date', '>=', record.date_start),
                ('work_date', '<=', record.date_end),
                ('state', '=', 'delivered'),
            ])
            linked_activity_ids = self.env['caramia.work.log'].search([
                ('labor_activity_id', 'in', activities.ids),
            ]).mapped('labor_activity_id').ids
            for activity in activities.filtered(lambda item: item.id not in linked_activity_ids):
                self.env['caramia.work.log'].create({
                    'paysheet_id': record.id,
                    'labor_activity_id': activity.id,
                    'date': activity.work_date,
                    'pairs_qty': activity.pairs_qty,
                    'price_per_pair': activity.price_per_pair,
                    'extra_amount': activity.extra_amount,
                    'extra_note': activity.extra_note,
                })
        return True

    def action_confirm(self):
        for record in self:
            if not record.work_log_ids:
                raise UserError('Agregue al menos un registro de trabajo antes de confirmar.')
            record.work_log_ids.mapped('labor_activity_id').filtered(
                lambda item: item.state == 'delivered'
            ).write({'state': 'settled'})
            record.write({'state': 'confirmed'})

    def action_pay(self):
        self.filtered(lambda record: record.state == 'confirmed').write({'state': 'paid'})


class HrEmployeePaysheetSummary(models.Model):
    _inherit = 'hr.employee'

    paysheet_ids = fields.One2many('caramia.weekly.paysheet', 'employee_id', string='Liquidaciones')
    paid_amount_accumulated = fields.Monetary(
        string='Pago semanal acumulado', compute='_compute_paysheet_summary',
        currency_field='company_currency_id'
    )
    annual_reserve_accumulated = fields.Monetary(
        string='Reserva anual acumulada', compute='_compute_paysheet_summary',
        currency_field='company_currency_id'
    )
    paid_paysheet_count = fields.Integer(string='Liquidaciones pagadas', compute='_compute_paysheet_summary')
    company_currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    def _compute_paysheet_summary(self):
        for employee in self:
            paid_paysheets = employee.paysheet_ids.filtered(lambda paysheet: paysheet.state == 'paid')
            employee.paid_amount_accumulated = sum(paid_paysheets.mapped('net_amount'))
            employee.annual_reserve_accumulated = sum(paid_paysheets.mapped('annual_reserve_amount'))
            employee.paid_paysheet_count = len(paid_paysheets)

    def action_view_paid_paysheets(self):
        self.ensure_one()
        action = self.env.ref('caramia_payroll.action_caramia_weekly_paysheet').read()[0]
        action['domain'] = [('employee_id', '=', self.id), ('state', '=', 'paid')]
        action['context'] = {'default_employee_id': self.id}
        return action
