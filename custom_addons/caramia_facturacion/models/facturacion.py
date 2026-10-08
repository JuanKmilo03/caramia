from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CaramiaFacturacion(models.Model):
    _name = 'cara.mia.facturacion'
    _description = 'Facturación / Remisión'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_facturacion desc, id desc'

    name = fields.Char(string='N° Facturación', required=True, copy=False, readonly=True, default='Nuevo', tracking=True)
    
    # Selección del Cliente y datos automáticos
    cliente_id = fields.Many2one('cara.mia.cliente', string='Cliente', required=True, tracking=True)
    cliente_identificador = fields.Char(related='cliente_id.cliente_id', string='ID Cliente', readonly=True)
    cliente_telefono = fields.Char(related='cliente_id.telefono_cliente', string='Teléfono', readonly=True)
    cliente_direccion = fields.Text(related='cliente_id.direccion', string='Dirección', readonly=True)
    
    # Líneas de la facturación (Múltiples órdenes)
    linea_ids = fields.One2many('cara.mia.facturacion.linea', 'facturacion_id', string='Artículos / Órdenes')

    # Fechas y Detalles
    pedido_nro = fields.Char(string='Pedido N°')
    fecha_facturacion = fields.Date(string='Fecha', default=fields.Date.context_today, required=True, tracking=True)
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento', required=True)
    forma_pago = fields.Selection([
        ('contado', 'Contado'),
        ('credito', 'Crédito')
    ], string='Forma de Pago', required=True, default='contado')

    # Cálculos y Valores
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    total_general = fields.Monetary(string='Total', compute='_compute_totales', store=True)
    saldo_pendiente = fields.Monetary(string='Saldo', compute='_compute_totales', store=True)

    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida'),
        ('pagada', 'Pagada')
    ], string='Estado', default='borrador', tracking=True)

    @api.depends('linea_ids.total_linea')
    def _compute_totales(self):
        for rec in self:
            rec.total_general = sum(line.total_linea for line in rec.linea_ids)
            rec.saldo_pendiente = rec.total_general if rec.estado != 'pagada' else 0.0

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

    def action_cancelar(self):
        for rec in self:
            rec.write({'estado': 'borrador'})

    def action_imprimir_remision(self):
        # Llama a la acción del reporte PDF que creamos anteriormente
        return self.env.ref('caramia_facturacion.action_report_remision_doble').report_action(self)


class CaramiaFacturacionLinea(models.Model):
    _name = 'cara.mia.facturacion.linea'
    _description = 'Línea de Facturación'

    facturacion_id = fields.Many2one('cara.mia.facturacion', ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='facturacion_id.currency_id')

    # Selección de la Orden de Producción
    produccion_id = fields.Many2one('cara.mia.produccion', string='Orden / Código', required=True)
    
    descripcion = fields.Char(string='Descripción', compute='_compute_descripcion', store=True)
    
    # Tallas extraídas de la orden
    talla_21 = fields.Integer(related='produccion_id.talla_21', string='21')
    talla_22 = fields.Integer(related='produccion_id.talla_22', string='22')
    talla_23 = fields.Integer(related='produccion_id.talla_23', string='23')
    talla_24 = fields.Integer(related='produccion_id.talla_24', string='24')
    talla_25 = fields.Integer(related='produccion_id.talla_25', string='25')
    talla_26 = fields.Integer(related='produccion_id.talla_26', string='26')
    talla_27 = fields.Integer(related='produccion_id.talla_27', string='27')
    talla_28 = fields.Integer(related='produccion_id.talla_28', string='28')
    talla_29 = fields.Integer(related='produccion_id.talla_29', string='29')
    talla_30 = fields.Integer(related='produccion_id.talla_30', string='30')
    talla_31 = fields.Integer(related='produccion_id.talla_31', string='31')
    talla_32 = fields.Integer(related='produccion_id.talla_32', string='32')
    talla_33 = fields.Integer(related='produccion_id.talla_33', string='33')
    talla_34 = fields.Integer(related='produccion_id.talla_34', string='34')
    talla_35 = fields.Integer(related='produccion_id.talla_35', string='35')
    talla_36 = fields.Integer(related='produccion_id.talla_36', string='36')
    talla_37 = fields.Integer(related='produccion_id.talla_37', string='37')
    talla_38 = fields.Integer(related='produccion_id.talla_38', string='38')
    talla_39 = fields.Integer(related='produccion_id.talla_39', string='39')
    talla_40 = fields.Integer(related='produccion_id.talla_40', string='40')

    cantidad = fields.Integer(related='produccion_id.total_pares', string='Cant')
    valor_unitario = fields.Monetary(string='Valor', required=True, default=0.0)
    total_linea = fields.Monetary(string='Total', compute='_compute_total_linea', store=True)

    # NUEVA FUNCIÓN: Traer el precio sugerido de la referencia
    @api.onchange('produccion_id')
    def _onchange_produccion_id(self):
        for rec in self:
            if rec.produccion_id and rec.produccion_id.referencia_id:
                rec.valor_unitario = rec.produccion_id.referencia_id.precio_venta_sugerido
            else:
                rec.valor_unitario = 0.0

    @api.depends('produccion_id')
    def _compute_descripcion(self):
        for rec in self:
            if rec.produccion_id and rec.produccion_id.referencia_id:
                rec.descripcion = f"{rec.produccion_id.referencia_id.nombre_modelo} - {rec.produccion_id.color} - {rec.produccion_id.material}"
            else:
                rec.descripcion = ""

    @api.depends('cantidad', 'valor_unitario')
    def _compute_total_linea(self):
        for rec in self:
            rec.total_linea = rec.cantidad * rec.valor_unitario