from odoo import models, fields, api

class ReferenciaCalzado(models.Model):
    _name = 'cara.mia.referencia'
    _description = 'Referencia y Ficha Técnica de Calzado'
    _rec_name = 'nombre_modelo'

    codigo_referencia = fields.Char(
        string='Código de Referencia',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: 'Nuevo'
    )
    nombre_modelo = fields.Char(string='Nombre del Modelo', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    imagen_zapato = fields.Image(string='Fotografía del Calzado')
    descripcion = fields.Text(string='Descripción y Observaciones')
    estado = fields.Selection([
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo')
    ], string='Estado', default='activo', tracking=True)

    insumo_ids = fields.One2many(
        'cara.mia.insumo.referencia', 'referencia_id',
        string='Ficha Técnica de Insumos'
    )
    labor_ids = fields.One2many(
        'cara.mia.precio.labor.ref', 'referencia_id',
        string='Labores de Producción'
    )

    precio_total_labor = fields.Monetary(
        string='Costo Total de Mano de Obra',
        compute='_compute_precio_total_labor',
        store=True,
        currency_field='currency_id'
    )
    costo_total_insumos = fields.Monetary(
        string='Costo Total de Insumos',
        compute='_compute_costo_total_insumos',
        store=True,
        currency_field='currency_id'
    )
    costo_total_produccion = fields.Monetary(
        string='Costo Total de Producción',
        compute='_compute_costo_total_produccion',
        store=True,
        currency_field='currency_id'
    )

    @api.depends('labor_ids.tarifa_pago')
    def _compute_precio_total_labor(self):
        for record in self:
            record.precio_total_labor = sum(record.labor_ids.mapped('tarifa_pago'))

    @api.depends('insumo_ids.costo_estimado')
    def _compute_costo_total_insumos(self):
        for record in self:
            record.costo_total_insumos = sum(record.insumo_ids.mapped('costo_estimado'))

    @api.depends('costo_total_insumos', 'precio_total_labor')
    def _compute_costo_total_produccion(self):
        for record in self:
            record.costo_total_produccion = (
                record.costo_total_insumos + record.precio_total_labor
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codigo_referencia', 'Nuevo') == 'Nuevo':
                vals['codigo_referencia'] = (
                    self.env['ir.sequence'].next_by_code('cara.mia.referencia.sequence')
                    or 'Nuevo'
                )
        return super().create(vals_list)