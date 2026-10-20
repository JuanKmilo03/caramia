from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class CaramiaFacturacion(models.Model):
    _name = 'cara.mia.facturacion'
    _description = 'Facturación / Remisión'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_facturacion desc, id desc'

    name = fields.Char(string='N° Factura', required=True, copy=False, readonly=True, default='Nuevo', tracking=True)

    # Selección del Cliente y datos automáticos
    cliente_id = fields.Many2one('cara.mia.cliente', string='Cliente', required=True, tracking=True)
    cliente_identificador = fields.Char(related='cliente_id.cliente_id', string='ID Cliente', readonly=True)
    cliente_telefono = fields.Char(related='cliente_id.telefono_cliente', string='Teléfono', readonly=True)
    cliente_direccion = fields.Text(related='cliente_id.direccion', string='Dirección', readonly=True)

    # Líneas de la facturación (Múltiples órdenes)
    linea_ids = fields.One2many('cara.mia.facturacion.linea', 'facturacion_id', string='Artículos / Órdenes')

    # Fechas y Detalles
    fecha_facturacion = fields.Date(string='Fecha de Facturación', default=fields.Date.context_today, required=True, tracking=True)
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento', required=True)
    forma_pago = fields.Selection([
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ], string='Forma de Pago', required=True, default='contado')

    # Cálculos y Valores
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    total_general = fields.Monetary(string='Total', compute='_compute_totales', store=True)
    saldo_pendiente = fields.Monetary(string='Saldo', compute='_compute_saldo', store=True)

    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ], string='Estado', default='borrador', tracking=True)

    # Cuentas de cobro generadas al emitir (solo una puede estar activa)
    cuenta_ids = fields.One2many('cara.mia.cuenta.cobro', 'factura_id', string='Cuentas de Cobro')

    @api.depends('linea_ids.total_linea')
    def _compute_totales(self):
        for rec in self:
            rec.total_general = sum(rec.linea_ids.mapped('total_linea'))

    @api.depends('estado', 'total_general', 'cuenta_ids.saldo_pendiente', 'cuenta_ids.estado')
    def _compute_saldo(self):
        for rec in self:
            cuenta = rec._cuenta_vigente()
            if cuenta:
                rec.saldo_pendiente = cuenta.saldo_pendiente
            elif rec.estado == 'pagada':
                rec.saldo_pendiente = 0.0
            else:
                rec.saldo_pendiente = rec.total_general

    def _cuenta_vigente(self):
        """Cuenta de cobro no anulada de la factura (si existe)."""
        self.ensure_one()
        return self.cuenta_ids.filtered(lambda c: c.estado != 'anulada')[:1]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('cara.mia.facturacion.seq') or 'Nuevo'
        return super().create(vals_list)

    def action_emitir(self):
        for rec in self:
            if not rec.linea_ids:
                raise ValidationError("Debe agregar al menos una orden de producción para emitir la factura/remisión.")
            if rec.total_general <= 0:
                raise ValidationError("El total de la factura debe ser mayor a cero.")

            rec.write({'estado': 'emitida'})

            for linea in rec.linea_ids:
                if linea.produccion_id:
                    linea.produccion_id.write({'factura_id': rec.id})

            rec._crear_cuenta_cobro()

    def _crear_cuenta_cobro(self):
        """Abre la cuenta de cobro de las facturas emitidas que aún no tienen una activa."""
        Cuenta = self.env['cara.mia.cuenta.cobro']
        for rec in self.filtered(lambda f: f.estado == 'emitida' and not f._cuenta_vigente()):
            Cuenta.create({'factura_id': rec.id})

    def action_cancelar(self):
        for rec in self:
            if rec._cuenta_vigente():
                raise UserError(
                    "La factura %s tiene una cuenta de cobro activa.\n"
                    "Anule primero la cuenta de cobro para poder devolverla a borrador." % rec.name
                )
            rec.write({'estado': 'borrador'})

    def action_ver_cuenta(self):
        self.ensure_one()
        cuenta = self._cuenta_vigente() or self.cuenta_ids[:1]
        if not cuenta:
            raise UserError("Esta factura todavía no tiene cuenta de cobro.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cuenta de Cobro',
            'res_model': 'cara.mia.cuenta.cobro',
            'res_id': cuenta.id,
            'view_mode': 'form',
        }

    def action_imprimir_remision(self):
        # Llama a la acción del reporte PDF que creamos anteriormente
        return self.env.ref('caramia_facturacion.action_report_remision_doble').report_action(self)


class CaramiaProductionInherit(models.Model):
    _inherit = 'cara.mia.produccion'

    factura_id = fields.Many2one(
        'cara.mia.facturacion',
        string='Factura N°',
        readonly=True,
        tracking=True,
    )