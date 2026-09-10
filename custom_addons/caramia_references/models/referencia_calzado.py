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
    
    tipo_tarifa_header = fields.Selection([
        ('manual', 'Manual / Digitar libre'),
        ('1', 'Precio Sugerido 1'),
        ('2', 'Precio Sugerido 2')
    ], string='Origen de Precios', default='manual', tracking=True)

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
        string='Costo Estimado de Producción',
        compute='_compute_costo_total_produccion',
        store=True,
        currency_field='currency_id'
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        tipos_labor = self.env['cara.mia.tipo.labor'].search([])
        labor_lines = []
        for labor in tipos_labor:
            labor_lines.append((0, 0, {
                'tipo_labor_id': labor.id,
                'tarifa_pago': 0.0,
            }))
        res['labor_ids'] = labor_lines
        return res
    
    @api.depends('labor_ids.tarifa_pago')
    def _compute_precio_total_labor(self):
        for record in self:
            record.precio_total_labor = sum(record.labor_ids.mapped('tarifa_pago'))
            
    @api.onchange('tipo_tarifa_header')
    def _onchange_tipo_tarifa_header(self):
        for referencia in self:
            if referencia.tipo_tarifa_header == 'manual':
                continue
            for linea in referencia.labor_ids:
                if linea.tipo_labor_id:
                    if referencia.tipo_tarifa_header == '2':
                        linea.tarifa_pago = linea.tipo_labor_id.tarifa_especial or 0.0
                    elif referencia.tipo_tarifa_header == '1':
                        linea.tarifa_pago = linea.tipo_labor_id.tarifa_normal or 0.0

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