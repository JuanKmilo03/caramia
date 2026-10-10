from odoo import models, fields, api
from odoo.exceptions import ValidationError

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
        ('credito', 'Crédito')
    ], string='Forma de Pago', required=True, default='contado')

    # Cálculos y Valores
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    total_general = fields.Monetary(string='Total', compute='_compute_totales', store=True)
    saldo_pendiente = fields.Monetary(string='Saldo', compute='_compute_totales', store=True)

    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('emitida', 'Emitida')
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
            
            for linea in rec.linea_ids:
                if linea.produccion_id:
                    linea.produccion_id.write({'factura_id': rec.id})

    def action_cancelar(self):
        for rec in self:
            rec.write({'estado': 'borrador'})

    def action_imprimir_remision(self):
        # Llama a la acción del reporte PDF que creamos anteriormente
        return self.env.ref('caramia_facturacion.action_report_remision_doble').report_action(self)

class CaramiaProductionInherit(models.Model):
    _inherit = 'cara.mia.produccion'

    factura_id = fields.Many2one(
        'cara.mia.facturacion', 
        string='Factura N°', 
        readonly=True, 
        tracking=True
    )
