from odoo import api, fields, models


# 1. MODELO DE PRÉSTAMOS / DESCUENTOS (Líneas dentro del empleado)
class CaramiaPrestamo(models.Model):
    _name = 'cara.mia.prestamo'
    _description = 'Préstamo / Descuento a Empleado'
    _order = 'fecha desc, id desc'

    empleado_id = fields.Many2one(
        'cara.mia.empleado',
        string='Empleado',
        required=True,
        ondelete='cascade',
    )
    fecha = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        required=True,
    )
    monto = fields.Monetary(
        string='Monto',
        required=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='empleado_id.currency_id',
        readonly=True,
    )
    observaciones = fields.Text(string='Motivo / Observación')
    state = fields.Selection(
        [
            ('pending', 'En Deuda'),
            ('paid', 'Pagado'),
        ],
        string='Estado',
        default='pending',
        required=True,
    )


# 2. MODELO PRINCIPAL DE EMPLEADO
class CaramiaEmployee(models.Model):
    _name = 'cara.mia.empleado'
    _description = 'Empleado Caramia'
    _rec_name = 'nombre_empleado'

    empleado_id = fields.Char(
        string='Cédula', required=True, copy=False, index=True
    )
    nombre_empleado = fields.Char(string='Nombre Completo', required=True)
    telefono_empleado = fields.Char(string='Teléfono', required=True)

    tipo_labor_id = fields.Many2one(
        'cara.mia.tipo.labor',
        string='Labor',
        required=True,
        ondelete='restrict',
    )

    registro_trabajo_orden_ids = fields.One2many(
        'cara.mia.registro.trabajo.orden',
        'empleado_id',
        string='Historial de Trabajos',
    )

    # HISTORIAL DE LIQUIDACIONES RECIBIDAS
    historial_nomina_ids = fields.One2many(
        'cara.mia.pago.empleado.linea',
        'empleado_id',
        string='Historial de Nóminas',
        domain=[('state_pago', '=', 'done'), ('pagado', '=', True)],
    )

    # MONEDA POR DEFECTO DE LA COMPAÑÍA
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )

    # LISTA DE PRÉSTAMOS DEL EMPLEADO
    prestamo_ids = fields.One2many(
        'cara.mia.prestamo',
        'empleado_id',
        string='Préstamos / Descuentos',
    )

    # TOTAL ACUMULADO PENDIENTE DE COBRO
    total_prestamos_pendientes = fields.Monetary(
        string='Saldo Pendiente Préstamos',
        compute='_compute_prestamos_totales',
        currency_field='currency_id',
    )

    aplica_liquidacion = fields.Boolean(
        string='Aplica Liquidación',
        default=True,
        help='Si no se activa, no se le aplicará el descuento del 0.22% ni será registrado para liquidación en nómina.'
    )

    @api.depends('prestamo_ids', 'prestamo_ids.state', 'prestamo_ids.monto')
    def _compute_prestamos_totales(self):
        for emp in self:
            pendientes = emp.prestamo_ids.filtered(lambda p: p.state == 'pending')
            emp.total_prestamos_pendientes = sum(pendientes.mapped('monto'))

    def action_view_prestamos(self):
        """Acción del Smart Button"""
        self.ensure_one()
        return {
            'name': f'Préstamos de {self.nombre_empleado}',
            'type': 'ir.actions.act_window',
            'res_model': 'cara.mia.prestamo',
            'view_mode': 'list,form',
            'domain': [('empleado_id', '=', self.id)],
            'context': {'default_empleado_id': self.id},
        }

    _sql_constraints = [(
        'empleado_id_unique',
        'unique(empleado_id)',
        'La cédula/documento ingresado ya está registrado para otro empleado.',
    )]