from odoo import Command, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round


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
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
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
        ],
        string='Estado',
        default='draft',
        tracking=True,
    )

    def unlink(self):
        """Prohíbe estrictamente eliminar una liquidación procesada ('done')."""
        for rec in self:
            if rec.state == 'done':
                raise UserError(
                    "No se puede eliminar la liquidación "
                    f"'{rec.name or ''}' porque se encuentra finalizada y pagada."
                )
        return super().unlink()

    def action_cancelar(self):
        """Si está en borrador la elimina. Si está en 'done', lanza UserError."""
        for rec in self:
            if rec.state == 'done':
                raise UserError(
                    'No se puede cancelar una liquidación en estado Liquidado / Pagado.'
                )
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('linea_ids')
    def _compute_cantidad_empleados(self):
        for rec in self:
            rec.cantidad_empleados = len(rec.linea_ids)

    @api.depends(
        'fecha_corte',
        'linea_ids.empleado_id',
        'linea_ids.empleado_id.nombre_empleado',
    )
    def _compute_name(self):
        for rec in self:
            f_str = (
                rec.fecha_corte.strftime('%d/%m/%Y') if rec.fecha_corte else ''
            )
            num_emp = len(rec.linea_ids)
            if num_emp == 1:
                emp_name = (
                    rec.linea_ids[0].empleado_id.nombre_empleado or 'Empleado'
                )
                rec.name = f'Liquidación - {emp_name} ({f_str})'
            elif num_emp > 1:
                rec.name = f'Liquidación ({num_emp} Empleados) al {f_str}'
            else:
                rec.name = f'Liquidación Laboral ({f_str})'

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

    def action_cargar_todos_empleados(self):
        """Carga en lote a los empleados con fondo disponible (0.22% > 0.00).
        
        Aplica redondeo decimal estricto para evitar residuales flotantes (ej. 0.00001).
        """
        for rec in self:
            empleados = self.env['cara.mia.empleado'].search([])
            if not empleados:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Aviso',
                        'message': 'No hay empleados para liquidar.',
                        'type': 'warning',
                        'sticky': False,
                    },
                }

            emp_ids = empleados.ids
            precision = rec.currency_id.decimal_places or 2

            # Obtenemos préstamos pendientes
            prestamos_all = self.env['cara.mia.prestamo'].search([
                ('empleado_id', 'in', emp_ids),
                ('state', '=', 'pending'),
            ])
            prestamos_by_emp = {}
            for p in prestamos_all:
                prestamos_by_emp.setdefault(p.empleado_id.id, []).append(p)

            # Obtenemos retenciones realizadas en recibos procesados
            lineas_pago_all = self.env['cara.mia.pago.empleado.linea'].search([
                ('empleado_id', 'in', emp_ids),
                '|',
                ('pago_id.state', '=', 'done'),
                ('state_pago', '=', 'done'),
            ])
            retenciones_by_emp = {}
            for lp in lineas_pago_all:
                retenciones_by_emp[lp.empleado_id.id] = (
                    retenciones_by_emp.get(lp.empleado_id.id, 0.0)
                    + lp.reserva
                )

            # Obtenemos fondos ya liquidados previamente
            liqs_previas_all = self.env['cara.mia.liquidacion.linea'].search([
                ('empleado_id', 'in', emp_ids),
                ('liquidacion_id.state', '=', 'done'),
            ])
            usado_by_emp = {}
            for lp in liqs_previas_all:
                usado_by_emp[lp.empleado_id.id] = (
                    usado_by_emp.get(lp.empleado_id.id, 0.0)
                    + lp.fondo_reserva_acumulado
                )

            lineas_commands = [Command.clear()]
            for emp in empleados:
                total_retencion = retenciones_by_emp.get(emp.id, 0.0)
                total_ya_usado = usado_by_emp.get(emp.id, 0.0)
                
                # Redondeo exacto a 2 decimales para eliminar residuales de coma flotante
                fondo_disponible = float_round(
                    max(0.0, total_retencion - total_ya_usado),
                    precision_digits=precision
                )

                # FILTRO CON PRECISION MONETARIA: Solo si es estrictamente mayor a 0.00
                if float_compare(fondo_disponible, 0.0, precision_digits=precision) > 0:
                    prestamos = prestamos_by_emp.get(emp.id, [])
                    descuentos_commands = []
                    for p in prestamos:
                        fecha_p = (
                            p.fecha.strftime('%d/%m/%Y') if p.fecha else ''
                        )
                        motivo_txt = (
                            p.observaciones or 'Préstamo sin observación'
                        )
                        descuentos_commands.append(
                            Command.create({
                                'prestamo_id': p.id,
                                'monto': p.monto,
                                'razon': f'Préstamo ({fecha_p}): {motivo_txt}',
                            })
                        )

                    lineas_commands.append(
                        Command.create({
                            'empleado_id': emp.id,
                            'motivo': 'corte_anual',
                            'descuento_ids': descuentos_commands,
                        })
                    )

            # Si tras la evaluación no queda ningún empleado con saldo > 0.00
            if len(lineas_commands) <= 1:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Aviso',
                        'message': 'No hay empleados para liquidar.',
                        'type': 'warning',
                        'sticky': False,
                    },
                }

            rec.write({'linea_ids': lineas_commands})

    def action_confirmar_liquidacion(self):
        for rec in self:
            if not rec.linea_ids:
                raise ValidationError(
                    'Debe agregar al menos un empleado para liquidar.'
                )

            for linea in rec.linea_ids:
                prestamos = linea.descuento_ids.mapped('prestamo_id').filtered(
                    lambda p: p.state == 'pending'
                )
                if prestamos:
                    prestamos.write({'state': 'paid'})

            rec.write({'state': 'done'})


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
        if self.empleado_id:
            prestamos = self.env['cara.mia.prestamo'].search([
                ('empleado_id', '=', self.empleado_id.id),
                ('state', '=', 'pending'),
            ])
            descuentos = []
            for p in prestamos:
                fecha_p = p.fecha.strftime('%d/%m/%Y') if p.fecha else ''
                motivo_txt = p.observaciones or 'Préstamo sin observación'
                descuentos.append(
                    Command.create({
                        'prestamo_id': p.id,
                        'monto': p.monto,
                        'razon': f'Préstamo ({fecha_p}): {motivo_txt}',
                    })
                )
            self.descuento_ids = [Command.clear()] + descuentos
        else:
            self.descuento_ids = [Command.clear()]

    @api.depends('empleado_id')
    def _compute_fondo_reserva(self):
        for line in self:
            if line.empleado_id:
                precision = line.currency_id.decimal_places or 2
                lineas_pago = self.env['cara.mia.pago.empleado.linea'].search([
                    ('empleado_id', '=', line.empleado_id.id),
                    '|',
                    ('pago_id.state', '=', 'done'),
                    ('state_pago', '=', 'done'),
                ])
                total_retencion = sum(lineas_pago.mapped('reserva'))

                line_origin_id = line._origin.id if line._origin else 0
                liqs_previas = self.env['cara.mia.liquidacion.linea'].search([
                    ('empleado_id', '=', line.empleado_id.id),
                    ('liquidacion_id.state', '=', 'done'),
                    ('id', '!=', line_origin_id),
                ])
                total_ya_usado = sum(
                    liqs_previas.mapped('fondo_reserva_acumulado')
                )

                line.fondo_reserva_acumulado = float_round(
                    max(0.0, total_retencion - total_ya_usado),
                    precision_digits=precision,
                )
            else:
                line.fondo_reserva_acumulado = 0.0

    @api.depends('descuento_ids', 'descuento_ids.monto')
    def _compute_monto_descuentos(self):
        for line in self:
            line.monto_descuentos = sum(line.descuento_ids.mapped('monto'))

    @api.depends('fondo_reserva_acumulado', 'monto_descuentos')
    def _compute_monto_neto(self):
        for line in self:
            line.monto_neto = (
                line.fondo_reserva_acumulado - line.monto_descuentos
            )

    def action_abrir_descuentos(self):
        self.ensure_one()
        view = self.env.ref(
            'caramia_employee.view_caramia_liquidacion_descuento_modal',
            raise_if_not_found=False,
        ) or self.env.ref(
            'cara_mia.view_caramia_liquidacion_descuento_modal',
            raise_if_not_found=False,
        )

        view_id = (
            view.id
            if view
            else self.env['ir.ui.view']
            .search(
                [
                    ('model', '=', 'cara.mia.liquidacion.linea'),
                    ('name', '=', 'cara.mia.liquidacion.descuento.modal'),
                ],
                limit=1,
            )
            .id
        )

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
        'cara.mia.liquidacion.linea',
        string='Línea de Liquidación',
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        'res.currency', related='linea_id.currency_id'
    )
    empleado_id = fields.Many2one(
        'cara.mia.empleado',
        related='linea_id.empleado_id',
        string='Empleado',
        store=True,
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
        if self.prestamo_id:
            self.monto = self.prestamo_id.monto
            fecha_p = (
                self.prestamo_id.fecha.strftime('%d/%m/%Y')
                if self.prestamo_id.fecha
                else ''
            )
            obs = self.prestamo_id.observaciones or 'Sin observación'
            self.razon = f'Préstamo ({fecha_p}): {obs}'