from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class CaramiaLiquidacion(models.Model):
    _name = 'cara.mia.liquidacion'
    _description = 'Proceso de Liquidación Laboral'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_corte desc, id desc'

    name = fields.Char(
        string='Referencia',
        compute='_compute_name',
        store=True,
        readonly=True,
        copy=False,
    )

    fecha_corte = fields.Date(
        string='Fecha de Corte / Salida',
        default=fields.Date.context_today,
        required=True,
        help='Fecha hasta la cual se calculará el fondo acumulado.',
    )

    linea_ids = fields.One2many(
        'cara.mia.liquidacion.linea',
        'liquidacion_id',
        string='Detalle por Empleado',
    )

    cantidad_empleados = fields.Integer(
        string='N° Empleados',
        compute='_compute_cantidad_empleados',
        store=True,
    )

    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )

    total_fondo_disponible = fields.Monetary(
        string='Total Fondo 0.22% Acumulado',
        compute='_compute_totales_globales',
        store=True,
        currency_field='currency_id',
    )
    total_descuentos = fields.Monetary(
        string='Total Descuentos Aplicados',
        compute='_compute_totales_globales',
        store=True,
        currency_field='currency_id',
    )
    total_a_pagar = fields.Monetary(
        string='Total Neto A Pagar',
        compute='_compute_totales_globales',
        store=True,
        currency_field='currency_id',
    )

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('done', 'Liquidado / Pagado'),
            ('cancel', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
        tracking=True,
    )

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(
                    f"No es posible eliminar la liquidación '{rec.name or ''}' "
                    "porque ya se encuentra en estado 'Liquidado / Pagado'. "
                    'Debe cancelarla antes de poder borrarla.'
                )
        return super().unlink()

    @api.depends('linea_ids')
    def _compute_cantidad_empleados(self):
        for rec in self:
            rec.cantidad_empleados = len(rec.linea_ids)

    @api.depends('fecha_corte', 'linea_ids.empleado_id')
    def _compute_name(self):
        for rec in self:
            f_str = rec.fecha_corte.strftime('%d/%m/%Y') if rec.fecha_corte else ''
            num_emp = len(rec.linea_ids)
            if num_emp == 1:
                emp_name = rec.linea_ids[0].empleado_id.nombre_empleado or 'Empleado'
                rec.name = f"Liquidación - {emp_name} ({f_str})"
            elif num_emp > 1:
                rec.name = f"Liquidación ({num_emp} Empleados) al {f_str}"
            else:
                rec.name = f"Liquidación Laboral ({f_str})"

    @api.depends(
        'linea_ids',
        'linea_ids.fondo_reserva_acumulado',
        'linea_ids.monto_descuentos',
        'linea_ids.monto_neto',
    )
    def _compute_totales_globales(self):
        for rec in self:
            rec.total_fondo_disponible = sum(
                rec.linea_ids.mapped('fondo_reserva_acumulado')
            )
            rec.total_descuentos = sum(
                rec.linea_ids.mapped('monto_descuentos')
            )
            rec.total_a_pagar = sum(rec.linea_ids.mapped('monto_neto'))

    @api.onchange('linea_ids')
    def _onchange_linea_ids(self):
        """Actualiza la vista en tiempo real al agregar o modificar líneas."""
        self._compute_totales_globales()

    def action_cargar_todos_empleados(self):
        """Carga únicamente a los empleados que apliquen a liquidación y tengan un
        fondo acumulado disponible (> 0) o préstamos pendientes en estado 'pending'.
        """
        for rec in self:
            # Solo empleados marcados para liquidación
            empleados = self.env['cara.mia.empleado'].search([('aplica_liquidacion', '=', True)])
            if not empleados:
                raise ValidationError("No se encontraron empleados habilitados para liquidación.")

            lineas = [(5, 0, 0)]
            for emp in empleados:
                # 1. Préstamos pendientes ('pending')
                prestamos = self.env['cara.mia.prestamo'].search([
                    ('empleado_id', '=', emp.id),
                    ('state', '=', 'pending'),
                ])

                # 2. Retenciones del 0.22% en nóminas aprobadas
                lineas_pago = self.env['cara.mia.pago.empleado.linea'].search([
                    ('empleado_id', '=', emp.id),
                    ('state_pago', '=', 'done'),
                ])
                total_retencion = sum(lineas_pago.mapped('descuento_reserva'))

                # 3. Restar lo que ya se liquidó previamente
                liqs_previas = self.env['cara.mia.liquidacion.linea'].search([
                    ('empleado_id', '=', emp.id),
                    ('liquidacion_id.state', '=', 'done'),
                ])
                total_ya_usado = sum(liqs_previas.mapped('fondo_reserva_acumulado'))
                fondo_disponible = max(0.0, total_retencion - total_ya_usado)

                # Se liquida solo si tiene saldo retenido (> 0) o préstamos pendientes
                if fondo_disponible > 0 or prestamos:
                    descuentos = []
                    for p in prestamos:
                        fecha_p = p.fecha.strftime('%d/%m/%Y') if p.fecha else ''
                        motivo_txt = p.observaciones or 'Préstamo sin observación'
                        descuentos.append((0, 0, {
                            'prestamo_id': p.id,
                            'monto': p.monto,
                            'razon': f"Préstamo ({fecha_p}): {motivo_txt}",
                        }))

                    lineas.append((
                        0,
                        0,
                        {
                            'empleado_id': emp.id,
                            'motivo': 'corte_anual',
                            'descuento_ids': descuentos,
                        },
                    ))

            if len(lineas) == 1:
                raise ValidationError("No hay empleados con saldo acumulado del 0.22% o préstamos pendientes por liquidar.")

            rec.write({'linea_ids': lineas})
            # Forzar recálculo en la base de datos
            rec.linea_ids._compute_monto_descuentos()
            rec.linea_ids._compute_monto_neto()
            rec._compute_totales_globales()

    def action_confirmar_liquidacion(self):
        """Al confirmar, pasa la liquidación a 'done' y pasa los préstamos a 'paid'."""
        for rec in self:
            if not rec.linea_ids:
                raise ValidationError("Debe agregar al menos un empleado para liquidar.")
            
            for linea in rec.linea_ids:
                prestamos = linea.descuento_ids.mapped('prestamo_id').filtered(lambda p: p.state == 'pending')
                if prestamos:
                    prestamos.write({'state': 'paid'})

            rec.write({'state': 'done'})

    def action_cancelar(self):
        """Si se cancela la liquidación, vuelve los préstamos a 'pending'."""
        for rec in self:
            for linea in rec.linea_ids:
                prestamos = linea.descuento_ids.mapped('prestamo_id').filtered(lambda p: p.state == 'paid')
                if prestamos:
                    prestamos.write({'state': 'pending'})
            rec.write({'state': 'cancel'})


class CaramiaLiquidacionLinea(models.Model):
    _name = 'cara.mia.liquidacion.linea'
    _description = 'Detalle de Liquidación por Empleado'

    liquidacion_id = fields.Many2one(
        'cara.mia.liquidacion', string='Liquidación Madre', ondelete='cascade'
    )
    empleado_id = fields.Many2one(
        'cara.mia.empleado', string='Empleado', required=True
    )

    motivo = fields.Selection(
        [
            ('corte_anual', 'Corte de Fin de Año'),
            ('renuncia', 'Renuncia'),
            ('despido', 'Despido'),
        ],
        string='Motivo',
        default='corte_anual',
        required=True,
    )

    currency_id = fields.Many2one(
        'res.currency', related='liquidacion_id.currency_id'
    )

    fondo_reserva_acumulado = fields.Monetary(
        string='Fondo 0.22% Acumulado',
        compute='_compute_fondo_reserva',
        store=True,
        currency_field='currency_id',
    )

    descuento_ids = fields.One2many(
        'cara.mia.liquidacion.descuento',
        'linea_id',
        string='Descuentos Registrados',
    )
    monto_descuentos = fields.Monetary(
        string='Total Descuentos',
        compute='_compute_monto_descuentos',
        store=True,
        currency_field='currency_id',
    )

    monto_neto = fields.Monetary(
        string='Neto A Pagar',
        compute='_compute_monto_neto',
        store=True,
        currency_field='currency_id',
    )

    @api.onchange('empleado_id')
    def _onchange_empleado_id_cargar_prestamos(self):
        """Al seleccionar un empleado individualmente, auto-carga todos sus préstamos pendientes ('pending')."""
        if self.empleado_id:
            prestamos = self.env['cara.mia.prestamo'].search([
                ('empleado_id', '=', self.empleado_id.id),
                ('state', '=', 'pending'),
            ])
            descuentos = []
            for p in prestamos:
                fecha_p = p.fecha.strftime('%d/%m/%Y') if p.fecha else ''
                motivo_txt = p.observaciones or 'Préstamo sin observación'
                descuentos.append((0, 0, {
                    'prestamo_id': p.id,
                    'monto': p.monto,
                    'razon': f"Préstamo ({fecha_p}): {motivo_txt}",
                }))
            self.descuento_ids = descuentos
        else:
            self.descuento_ids = [(5, 0, 0)]

        self._compute_monto_descuentos()
        self._compute_monto_neto()

    @api.depends('empleado_id')
    def _compute_fondo_reserva(self):
        for line in self:
            if line.empleado_id:
                lineas_pago = self.env['cara.mia.pago.empleado.linea'].search([
                    ('empleado_id', '=', line.empleado_id.id),
                    ('state_pago', '=', 'done'),
                ])
                total_retencion = sum(lineas_pago.mapped('descuento_reserva'))

                liqs_previas = self.env['cara.mia.liquidacion.linea'].search([
                    ('empleado_id', '=', line.empleado_id.id),
                    ('liquidacion_id.state', '=', 'done'),
                    ('id', '!=', line.id),
                ])
                total_ya_usado = sum(liqs_previas.mapped('fondo_reserva_acumulado'))

                line.fondo_reserva_acumulado = max(0.0, total_retencion - total_ya_usado)
            else:
                line.fondo_reserva_acumulado = 0.0

    @api.depends('descuento_ids', 'descuento_ids.monto')
    def _compute_monto_descuentos(self):
        for line in self:
            line.monto_descuentos = sum(line.descuento_ids.mapped('monto'))

    @api.onchange('descuento_ids')
    def _onchange_descuento_ids(self):
        """Actualiza los subtotales en tiempo real al manipular descuentos."""
        self._compute_monto_descuentos()
        self._compute_monto_neto()

    @api.depends('fondo_reserva_acumulado', 'monto_descuentos')
    def _compute_monto_neto(self):
        for line in self:
            line.monto_neto = line.fondo_reserva_acumulado - line.monto_descuentos

    def action_abrir_descuentos(self):
        """Abre la ventana emergente/modal para ingresar o consultar descuentos."""
        self.ensure_one()
        
        view = (
            self.env.ref('caramia_employee.view_caramia_liquidacion_descuento_modal', raise_if_not_found=False)
            or self.env.ref('cara_mia.view_caramia_liquidacion_descuento_modal', raise_if_not_found=False)
        )
        
        view_id = view.id if view else self.env['ir.ui.view'].search([
            ('model', '=', 'cara.mia.liquidacion.linea'),
            ('name', '=', 'cara.mia.liquidacion.descuento.modal'),
        ], limit=1).id

        return {
            'name': f'Descuentos de {self.empleado_id.nombre_empleado or ""}',
            'type': 'ir.actions.act_window',
            'res_model': 'cara.mia.liquidacion.linea',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
        }

class CaramiaLiquidacionDescuento(models.Model):
    _name = 'cara.mia.liquidacion.descuento'
    _description = 'Registro Individual de Descuento en Liquidación'

    linea_id = fields.Many2one(
        'cara.mia.liquidacion.linea', string='Línea de Liquidación', ondelete='cascade'
    )
    currency_id = fields.Many2one(
        'res.currency', related='linea_id.currency_id'
    )
    empleado_id = fields.Many2one(
        'cara.mia.empleado', related='linea_id.empleado_id', string='Empleado', store=True
    )

    prestamo_id = fields.Many2one(
        'cara.mia.prestamo',
        string='Préstamo del Empleado',
        domain="[('empleado_id', '=', empleado_id), ('state', '=', 'pending')]",
        ondelete='set null',
    )

    monto = fields.Monetary(
        string='Monto ($)',
        required=True,
        currency_field='currency_id',
    )
    razon = fields.Char(
        string='Razón / Motivo del Descuento',
        required=True,
    )

    @api.onchange('prestamo_id')
    def _onchange_prestamo_id(self):
        """Al seleccionar un préstamo, autocompleta el monto y la razón."""
        if self.prestamo_id:
            self.monto = self.prestamo_id.monto
            fecha_p = self.prestamo_id.fecha.strftime('%d/%m/%Y') if self.prestamo_id.fecha else ''
            obs = self.prestamo_id.observaciones or 'Sin observación'
            self.razon = f"Préstamo ({fecha_p}): {obs}"