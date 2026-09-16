from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CaramiaRegistroTrabajo(models.Model):
    _name = 'cara.mia.registro.trabajo.orden'
    _description = 'Registro de Tiquetes / Trabajo Realizado'
    _order = 'fecha desc, id desc'

    # 1. Datos de Producción (Escaneo directo sobre produccion_id)
    produccion_id = fields.Many2one(
        'cara.mia.produccion', 
        string='Orden de Producción', 
        compute='_compute_produccion_id',
        store=True,
        readonly=True
    )
    orden_codigo = fields.Char(string='Código de Orden', required=True)


    fecha = fields.Date(
        string='Fecha de Registro', 
        default=fields.Date.context_today, 
        required=True
    )
    total_pares = fields.Integer(
        related='produccion_id.total_pares', 
        string='Pares', 
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency', 
        related='produccion_id.currency_id'
    )

    # 2. Datos del Operario (Opcional al inicio)
    empleado_id = fields.Many2one(
        'cara.mia.empleado', 
        string='Empleado / Operario', 
        required=True
    )
    tipo_labor_id = fields.Many2one(
        'cara.mia.tipo.labor', 
        related='empleado_id.tipo_labor_id', 
        store=True, 
        string='Labor Realizada',
        readonly=True
    )

    # 3. Liquidación
    tarifa_pago = fields.Monetary(
        string='Tarifa por Par', 
        compute='_compute_tarifa_pago', 
        store=True, 
        currency_field='currency_id'
    )
    subtotal = fields.Monetary(
        string='Subtotal a Pagar', 
        compute='_compute_subtotal', 
        store=True, 
        currency_field='currency_id'
    )
    
    estado = fields.Selection([
        ('sin_asignar', 'Sin Asignar'),
        ('pendiente', 'Pendiente de Liquidar'),
        ('pagado', 'Pagado en Nómina')
    ], string='Estado', compute='_compute_estado', store=True, default='sin_asignar')

    # 1. Cálculo automático en el servidor al cambiar orden_codigo
    @api.depends('orden_codigo')
    def _compute_produccion_id(self):
        for rec in self:
            if rec.orden_codigo:
                codigo_limpio = rec.orden_codigo.strip()
                orden = self.env['cara.mia.produccion'].search([('name', '=', codigo_limpio)], limit=1)
                rec.produccion_id = orden.id if orden else False
            else:
                rec.produccion_id = False

    # 2. Validaciones al guardar
    @api.constrains('orden_codigo', 'produccion_id')
    def _check_orden_valida(self):
        for rec in self:
            if rec.orden_codigo and not rec.produccion_id:
                raise ValidationError(
                    f"¡No se puede guardar el registro!\n\n"
                    f"La Orden de Producción '{rec.orden_codigo}' no existe en el sistema."
                )

    @api.constrains('produccion_id', 'empleado_id')
    def _check_labor_en_orden_produccion(self):
        for rec in self:
            if rec.produccion_id and rec.empleado_id and rec.tipo_labor_id:
                labores_validas = rec.produccion_id.labor_ids.mapped('tipo_labor_id')
                if rec.tipo_labor_id not in labores_validas:
                    raise ValidationError(
                        f"¡No se puede registrar este trabajo!\n\n"
                        f"El empleado '{rec.empleado_id.nombre_empleado}' realiza la labor '{rec.tipo_labor_id.name}', "
                        f"pero esta no está presupuestada en la Orden '{rec.produccion_id.name}'."
                    )

    @api.depends('empleado_id')
    def _compute_estado(self):
        for rec in self:
            if not rec.empleado_id:
                rec.estado = 'sin_asignar'
            elif rec.estado == 'pagado':
                rec.estado = 'pagado'
            else:
                rec.estado = 'pendiente'

    @api.depends('produccion_id', 'tipo_labor_id')
    def _compute_tarifa_pago(self):
        for rec in self:
            if rec.produccion_id and rec.tipo_labor_id:
                linea_labor = rec.produccion_id.labor_ids.filtered(
                    lambda l: l.tipo_labor_id == rec.tipo_labor_id
                )
                rec.tarifa_pago = linea_labor.tarifa_pago if linea_labor else 0.0
            else:
                rec.tarifa_pago = 0.0

    @api.depends('total_pares', 'tarifa_pago')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.total_pares * rec.tarifa_pago

    _sql_constraints = [
        (
            'orden_labor_unica', 
            'unique(produccion_id, tipo_labor_id)', 
            '¡Esta labor para esta orden de producción ya fue registrada y asignada previamente!'
        )
    ]