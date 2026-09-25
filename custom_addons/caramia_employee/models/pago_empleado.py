from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class CaramiaPagoEmpleado(models.Model):
    _name = 'cara.mia.pago.empleado'
    _description = 'Nómina de Empleados'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_fin desc, id desc'

    def _get_default_fecha_inicio(self):
        return fields.Date.today() - timedelta(days=7)

    name = fields.Char(
        string='Referencia de Nómina',
        compute='_compute_name',
        store=True,
        readonly=True,
        copy=False,
    )

    fecha_inicio = fields.Date(
        string='Desde',
        required=True,
        default=_get_default_fecha_inicio,
        help='Fecha inicial del período de nómina.',
    )
    fecha_fin = fields.Date(
        string='Hasta',
        required=True,
        default=fields.Date.context_today,
        help='Fecha final del período de nómina.',
    )
    fecha_nomina = fields.Date(
        string='Fecha de Realización',
        default=fields.Date.context_today,
        readonly=True,
    )

    linea_ids = fields.One2many(
        'cara.mia.pago.empleado.linea',
        'pago_id',
        string='Detalle por Empleado',
    )

    # TOTALES GLOBALES
    total_bruto = fields.Monetary(
        string='Total Labores',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
    )
    total_descontado = fields.Monetary(
        string='Descuento (0.22%)',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
    )
    total_neto = fields.Monetary(
        string='Total A Pagar',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
    )
    total_pagado = fields.Monetary(
        string='Valor Pagado',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('in_progress', 'En Proceso'),
            ('done', 'Finalizado'),
            ('cancel', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
        tracking=True,
    )

    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_name(self):
        for rec in self:
            if rec.fecha_inicio and rec.fecha_fin:
                f_inicio = rec.fecha_inicio.strftime('%d/%m/%Y')
                f_fin = rec.fecha_fin.strftime('%d/%m/%Y')
                rec.name = f"Nómina del {f_inicio} al {f_fin}"
            else:
                rec.name = "Nómina de Empleados"

    @api.depends(
        'linea_ids.monto_bruto',
        'linea_ids.descuento_reserva',
        'linea_ids.monto_neto',
        'linea_ids.pagado',
    )
    def _compute_totales(self):
        for rec in self:
            rec.total_bruto = sum(rec.linea_ids.mapped('monto_bruto'))
            rec.total_descontado = sum(rec.linea_ids.mapped('descuento_reserva'))
            rec.total_neto = sum(rec.linea_ids.mapped('monto_neto'))

            lineas_pagadas = rec.linea_ids.filtered(lambda l: l.pagado)
            rec.total_pagado = sum(lineas_pagadas.mapped('monto_neto'))

    def action_calcular_pagos(self):
        for rec in self:
            if rec.fecha_inicio > rec.fecha_fin:
                raise ValidationError(
                    "La fecha 'Desde' no puede ser mayor a la fecha 'Hasta'."
                )

            tiquetes = self.env['cara.mia.registro.trabajo.orden'].search([
                ('fecha', '>=', rec.fecha_inicio),
                ('fecha', '<=', rec.fecha_fin),
                ('estado', '=', 'pendiente'),
                ('empleado_id', '!=', False),
            ])

            lineas = [(5, 0, 0)]
            empleados = tiquetes.mapped('empleado_id')

            for emp in empleados:
                tiquetes_emp = tiquetes.filtered(lambda t: t.empleado_id == emp)
                monto_bruto = sum(tiquetes_emp.mapped('subtotal'))
                pares_totales = sum(tiquetes_emp.mapped('total_pares'))

                lineas.append((
                    0,
                    0,
                    {
                        'empleado_id': emp.id,
                        'pagado': False,  # Checkbox de pago
                        'total_pares': pares_totales,
                        'monto_bruto': monto_bruto,
                        'tiquete_ids': [(6, 0, tiquetes_emp.ids)],
                    },
                ))

            rec.write({'linea_ids': lineas, 'state': 'in_progress'})

    def action_confirmar_pago(self):
        for rec in self:
            if not rec.linea_ids:
                raise ValidationError(
                    "No hay empleados agregados en esta nómina."
                )

            # Validar que todos los empleados de la nómina estén marcados como pagados
            lines_sin_pagar = rec.linea_ids.filtered(lambda l: not l.pagado)
            if lines_sin_pagar:
                empleados_pendientes = ", ".join(
                    lines_sin_pagar.mapped('empleado_id.nombre_empleado')
                )
                raise ValidationError(
                    f"No se puede aprobar la nómina porque existen empleados sin marcar como pagados:\n- {empleados_pendientes}"
                )

            # Marcar tiquetes de trabajo como pagados
            todos_los_tiquetes = rec.linea_ids.mapped('tiquete_ids')
            if todos_los_tiquetes:
                todos_los_tiquetes.write({'estado': 'pagado'})

            # Cambiar estado de la nómina a 'done'
            rec.write({'state': 'done', 'fecha_nomina': fields.Date.today()})

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(
                    "No se puede eliminar una nómina que ya ha sido finalizada."
                )
            tiquetes = rec.linea_ids.mapped('tiquete_ids')
            if tiquetes:
                tiquetes.write({'estado': 'pendiente'})
        return super().unlink()


class CaramiaPagoEmpleadoLinea(models.Model):
    _name = 'cara.mia.pago.empleado.linea'
    _description = 'Línea de Liquidación por Empleado'

    pago_id = fields.Many2one(
        'cara.mia.pago.empleado', string='Liquidación', ondelete='cascade'
    )
    empleado_id = fields.Many2one(
        'cara.mia.empleado', string='Empleado', required=True
    )
    
    # Campo relacionado para verificar la opción en la línea
    aplica_liquidacion = fields.Boolean(
        related='empleado_id.aplica_liquidacion',
        string='Aplica Liquidación',
        store=True,
    )

    pagado = fields.Boolean(
        string='¿Pagado?',
        default=False,
        help='Marque este campo una vez le haya entregado el dinero al empleado.',
    )

    fecha_inicio = fields.Date(
        related='pago_id.fecha_inicio', string='Desde', store=True
    )
    fecha_fin = fields.Date(
        related='pago_id.fecha_fin', string='Hasta', store=True
    )
    fecha_pago = fields.Date(
        related='pago_id.fecha_nomina', string='Fecha Pago', store=True
    )
    state_pago = fields.Selection(
        related='pago_id.state', string='Estado Nómina', store=True
    )

    total_pares = fields.Integer(string='Pares Elaborados', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', related='pago_id.currency_id'
    )

    monto_bruto = fields.Monetary(
        string='Monto Bruto', readonly=True, currency_field='currency_id'
    )
    descuento_reserva = fields.Monetary(
        string='Descuento (0.22%)',
        compute='_compute_montos',
        store=True,
        currency_field='currency_id',
    )
    monto_neto = fields.Monetary(
        string='Valor a Pagar',
        compute='_compute_montos',
        store=True,
        currency_field='currency_id',
    )

    tiquete_ids = fields.Many2many(
        comodel_name='cara.mia.registro.trabajo.orden',
        relation='caramia_pago_linea_tiquete_rel',
        column1='pago_linea_id',
        column2='tiquete_id',
        string='Tiquetes Incluidos',
    )

    @api.depends('monto_bruto', 'aplica_liquidacion')
    def _compute_montos(self):
        for line in self:
            if line.aplica_liquidacion:
                line.descuento_reserva = line.monto_bruto * 0.0022
            else:
                line.descuento_reserva = 0.0
            line.monto_neto = line.monto_bruto - line.descuento_reserva