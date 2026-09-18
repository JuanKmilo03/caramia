from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class CaramiaPagoEmpleado(models.Model):
    _name = 'cara.mia.pago.empleado'
    _description = 'Liquidación y Pago a Empleados'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_fin desc, id desc'

    def _get_default_fecha_inicio(self):
        """ Retorna 7 días (1 semana) antes de la fecha actual """
        return fields.Date.today() - timedelta(days=7)

    name = fields.Char(string='Referencia de Pago', required=True, copy=False, readonly=True, default='Nuevo')
    
    # --- RANGO DE FECHAS EN LA PARTE SUPERIOR ---
    fecha_inicio = fields.Date(
        string='Desde', 
        required=True, 
        default=_get_default_fecha_inicio,
        help="Fecha inicial para calcular los trabajos acumulados de todos los empleados."
    )
    fecha_fin = fields.Date(
        string='Hasta', 
        required=True, 
        default=fields.Date.context_today,
        help="Fecha final para calcular los trabajos acumulados de todos los empleados."
    )
    fecha_pago = fields.Date(string='Fecha de Liquidación', default=fields.Date.context_today, readonly=True)

    linea_ids = fields.One2many('cara.mia.pago.empleado.line', 'pago_id', string='Detalle por Empleado')

    # TOTALES DE LA LIQUIDACIÓN
    total_bruto = fields.Monetary(string='Total Ganado', compute='_compute_totales', store=True, currency_field='currency_id')
    total_descuentos = fields.Monetary(string='Total Descuentos', compute='_compute_totales', store=True, currency_field='currency_id')
    total_neto = fields.Monetary(string='Total A Pagar', compute='_compute_totales', store=True, currency_field='currency_id')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Pagado / Finalizado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    @api.depends('linea_ids.monto_bruto', 'linea_ids.descuento')
    def _compute_totales(self):
        for rec in self:
            rec.total_bruto = sum(rec.linea_ids.mapped('monto_bruto'))
            rec.total_descuentos = sum(rec.linea_ids.mapped('descuento'))
            rec.total_neto = sum(rec.linea_ids.mapped('monto_neto'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                # Coincide exactamente con el 'code' definido en ir_sequence_data.xml
                vals['name'] = self.env['ir.sequence'].next_by_code('cara.mia.pago.empleado') or 'Nuevo'
        return super().create(vals_list)

    def action_calcular_pagos(self):
        """ Busca los tiquetes pendientes dentro del rango de fechas y agrupa por empleado """
        for rec in self:
            if rec.fecha_inicio > rec.fecha_fin:
                raise ValidationError("La fecha 'Desde' no puede ser mayor a la fecha 'Hasta'.")

            # 1. Buscar tiquetes pendientes en el rango de fechas
            tiquetes = self.env['cara.mia.registro.trabajo.orden'].search([
                ('fecha', '>=', rec.fecha_inicio),
                ('fecha', '<=', rec.fecha_fin),
                ('estado', '=', 'pendiente'),
                ('empleado_id', '!=', False)
            ])

            # 2. Comando ORM (5, 0, 0) para limpiar de forma segura las líneas anteriores
            lineas = [(5, 0, 0)]

            # 3. Agrupar tiquetes por empleado
            empleados = tiquetes.mapped('empleado_id')
            for emp in empleados:
                tiquetes_emp = tiquetes.filtered(lambda t: t.empleado_id == emp)
                monto_bruto = sum(tiquetes_emp.mapped('subtotal'))
                pares_totales = sum(tiquetes_emp.mapped('total_pares'))

                lineas.append((0, 0, {
                    'empleado_id': emp.id,
                    'total_pares': pares_totales,
                    'monto_bruto': monto_bruto,
                    'descuento': 0.0,
                    'tiquete_ids': [(6, 0, tiquetes_emp.ids)],
                }))

            # 4. Escribir los cambios en la BD para forzar el renderizado en la interfaz
            rec.write({'linea_ids': lineas})

    def action_confirmar_pago(self):
        """ Marca los tiquetes procesados de todos los empleados como PAGADOS """
        for rec in self:
            todos_los_tiquetes = rec.linea_ids.mapped('tiquete_ids')
            if todos_los_tiquetes:
                todos_los_tiquetes.write({'estado': 'pagado'})
            rec.write({'state': 'done', 'fecha_pago': fields.Date.today()})

    def unlink(self):
        """ Al borrar la liquidación (en cualquier estado), fuerza que todos los tiquetes vuelvan a 'pendiente' """
        for rec in self:
            tiquetes = rec.linea_ids.mapped('tiquete_ids')
            if tiquetes:
                tiquetes.write({'estado': 'pendiente'})
        return super().unlink()


class CaramiaPagoEmpleadoLine(models.Model):
    _name = 'cara.mia.pago.empleado.line'
    _description = 'Línea de Liquidación por Empleado'

    pago_id = fields.Many2one('cara.mia.pago.empleado', string='Liquidación', ondelete='cascade')
    empleado_id = fields.Many2one('cara.mia.empleado', string='Empleado', required=True)
    total_pares = fields.Integer(string='Pares Elaborados', readonly=True)

    currency_id = fields.Many2one('res.currency', related='pago_id.currency_id')
    monto_bruto = fields.Monetary(string='Ganado (Bruto)', readonly=True, currency_field='currency_id')
    descuento = fields.Monetary(string='Descuento / Vale', default=0.0, currency_field='currency_id')
    monto_neto = fields.Monetary(string='A Pagar (Neto)', compute='_compute_monto_neto', store=True, currency_field='currency_id')
    
    observaciones = fields.Char(string='Motivo Descuento / Nota')
    tiquete_ids = fields.Many2many('cara.mia.registro.trabajo.orden', string='Tiquetes Incluidos')

    @api.depends('monto_bruto', 'descuento')
    def _compute_monto_neto(self):
        for line in self:
            line.monto_neto = line.monto_bruto - line.descuento