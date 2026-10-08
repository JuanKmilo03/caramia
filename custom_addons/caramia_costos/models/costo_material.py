from odoo import models, fields, api


class CaramiaCostoMaterialLine(models.Model):
    _name = 'caramia.costo.material.line'
    _description = 'Línea de Material - Hoja de Costos'

    costo_id = fields.Many2one(
        'caramia.costo',
        string='Cotización',
        required=True,
        ondelete='cascade'
    )
    insumo_catalogo_id = fields.Many2one(
        'cara.mia.insumo.catalogo',
        string='Insumo del Catálogo'
    )
    tipo_componente_id = fields.Many2one(
        'cara.mia.tipo.componente',
        string='Tipo de Componente'
    )
    unidad_medida = fields.Selection([
        ('cm', 'Cm'),
        ('mts', 'Mts'),
        ('pares', 'Pares'),
        ('und', 'Unidad'),
    ], string='Unidad')

    cantidad_docena = fields.Float(
        string='Cantidad x Lote',
        default=0.0,
        digits=(16, 4),
        help='Cantidad necesaria para producir una docena de pares'
    )
    precio_unitario = fields.Monetary(
        string='Precio Unitario',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='costo_id.currency_id',
        store=True
    )

    costo_docena = fields.Monetary(
        string='Costo x Lote',
        compute='_compute_costos',
        store=True,
        currency_field='currency_id'
    )
    costo_par = fields.Monetary(
        string='Costo x Par',
        compute='_compute_costos',
        store=True,
        currency_field='currency_id'
    )
    cantidad_par = fields.Float(
        string='Cantidad x Par',
        compute='_compute_costos',
        store=True,
        digits=(16, 4),
        help='Cantidad por par = cantidad docena ÷ lote'
    )

    @api.depends(
        'cantidad_docena',
        'precio_unitario',
        'costo_id.cantidad_lote'
    )
    def _compute_costos(self):
        for rec in self:
            lote = rec.costo_id.cantidad_lote or 12
            rec.costo_docena = rec.cantidad_docena * rec.precio_unitario
            rec.costo_par = rec.costo_docena / lote if lote else 0.0
            rec.cantidad_par = rec.cantidad_docena / lote if lote else 0.0

    @api.onchange('insumo_catalogo_id')
    def _onchange_insumo_catalogo_id(self):
        if self.insumo_catalogo_id:
            cat = self.insumo_catalogo_id
            self.unidad_medida = cat.unidad_medida
            self.tipo_componente_id = cat.tipo_componente_id.id
            self.precio_unitario = cat.costo_referencia or 0.0