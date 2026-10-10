from odoo import models, fields, api
from odoo.exceptions import ValidationError

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
                rec.descripcion = f"{rec.produccion_id.referencia_id.nombre_modelo}"
            else:
                rec.descripcion = ""

    @api.depends('cantidad', 'valor_unitario')
    def _compute_total_linea(self):
        for rec in self:
            rec.total_linea = rec.cantidad * rec.valor_unitario