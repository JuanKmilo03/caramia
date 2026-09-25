from odoo import models, fields, api
from odoo.exceptions import UserError

class CaramiaCosto(models.Model):
    _name = 'caramia.costo'
    _description = 'Cotización y Hoja de Costos de Calzado'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Nº Cotización', required=True, readonly=True, default='Nuevo', copy=False)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Moneda')
    
    fecha = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    customer_id = fields.Many2one('caramia.customer', string='Cliente', tracking=True)
    referencia_id = fields.Many2one(
        'cara.mia.referencia', 
        string='Referencia / Modelo', 
        required=True, 
        tracking=True,
        domain="[('estado', '=', 'activo')]"
    )
    
    observaciones = fields.Text(string='Notas / Observaciones')
    
    # ⚠️ IMPORTANTE: Estas relaciones deben coincidir exactamente con el _name de los modelos de abajo
    material_ids = fields.One2many('caramia.costo.material.line', 'costo_id', string='Materiales e Insumos')
    labor_ids = fields.One2many('caramia.costo.labor.line', 'costo_id', string='Mano de Obra / Labores')

    total_materiales_par = fields.Monetary(string='Total Materiales / Par', compute='_compute_totales', store=True, currency_field='currency_id')
    total_labores_par = fields.Monetary(string='Total Labores / Par', compute='_compute_totales', store=True, currency_field='currency_id')
    costo_total_par = fields.Monetary(string='Costo Total / Par', compute='_compute_totales', store=True, currency_field='currency_id')
    costo_total_docena = fields.Monetary(string='Costo Total / Docena', compute='_compute_totales', store=True, currency_field='currency_id')

    porcentaje_margen = fields.Float(string='% Margen Ganancia', default=30.0)
    precio_venta_par = fields.Monetary(string='Precio Venta / Par', compute='_compute_totales', store=True, currency_field='currency_id')
    precio_venta_docena = fields.Monetary(string='Precio Venta / Docena', compute='_compute_totales', store=True, currency_field='currency_id')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('approved', 'Aprobado'),
        ('production', 'En Producción'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    production_id = fields.Many2one('caramia.production', string='Orden de Producción Creada', readonly=True)

    @api.depends('material_ids.costo_par', 'labor_ids.costo_par', 'porcentaje_margen')
    def _compute_totales(self):
        for rec in self:
            rec.total_materiales_par = sum(rec.material_ids.mapped('costo_par'))
            rec.total_labores_par = sum(rec.labor_ids.mapped('costo_par'))
            rec.costo_total_par = rec.total_materiales_par + rec.total_labores_par
            rec.costo_total_docena = rec.costo_total_par * 12.0
            
            margen_factor = 1.0 + (rec.porcentaje_margen / 100.0)
            rec.precio_venta_par = rec.costo_total_par * margen_factor
            rec.precio_venta_docena = rec.precio_venta_par * 12.0

    @api.onchange('referencia_id')
    def _onchange_referencia_id(self):
        if not self.referencia_id:
            self.material_ids = [fields.Command.clear()]
            self.labor_ids = [fields.Command.clear()]
            return

        lineas_mat = []
        for insumo_ref in self.referencia_id.insumo_ids:
            precio = insumo_ref.insumo_catalogo_id.costo_referencia or 0.0
            lineas_mat.append(fields.Command.create({
                'insumo_catalogo_id': insumo_ref.insumo_catalogo_id.id,
                'nombre': insumo_ref.insumo_catalogo_id.name,
                'unidad_medida': insumo_ref.unidad_medida,
                'cantidad': insumo_ref.cantidad,
                'precio_unitario': precio,
                'rendimiento_pares': 12.0,
            }))

        lineas_lab = []
        for labor_ref in self.referencia_id.labor_ids:
            lineas_lab.append(fields.Command.create({
                'tipo_labor_id': labor_ref.tipo_labor_id.id,
                'costo_par': labor_ref.tarifa_pago,
            }))

        self.material_ids = [fields.Command.clear()] + lineas_mat
        self.labor_ids = [fields.Command.clear()] + lineas_lab

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('caramia.costo.number') or 'Nuevo'
        return super().create(vals_list)

    def action_pass_to_production(self):
        self.ensure_one()
        if not self.customer_id:
            raise UserError("Debe seleccionar un Cliente antes de pasar a producción.")

        production_vals = {
            'customer_id': self.customer_id.id,
            'referencia_id': self.referencia_id.id,
            'description': f"Generado desde Cotización {self.name}.\nObservaciones: {self.observaciones or ''}",
            'company_id': self.company_id.id,
        }
        
        nueva_op = self.env['caramia.production'].create(production_vals)
        
        self.write({
            'state': 'production',
            'production_id': nueva_op.id
        })

        return {
            'name': 'Orden de Producción Creada',
            'type': 'ir.actions.act_window',
            'res_model': 'caramia.production',
            'res_id': nueva_op.id,
            'view_mode': 'form',
            'target': 'current',
        }


# MODELO HIJO 1: LÍNEA DE MATERIALES
class CaramiaCostoMaterialLine(models.Model):
    _name = 'caramia.costo.material.line'
    _description = 'Línea de Materiales para Cotización'

    costo_id = fields.Many2one('caramia.costo', string='Cotización', ondelete='cascade')
    insumo_catalogo_id = fields.Many2one('cara.mia.insumo.catalogo', string='Insumo Catálogo')
    nombre = fields.Char(string='Descripción / Material', required=True)
    unidad_medida = fields.Char(string='U.M.')
    
    cantidad = fields.Float(string='Medida / Cantidad', default=1.0, digits=(16, 2))
    precio_unitario = fields.Monetary(string='Precio Unitario', currency_field='currency_id')
    rendimiento_pares = fields.Float(string='Divisor (Pares)', default=12.0)
    
    costo_par = fields.Monetary(string='Costo / Par', compute='_compute_costo_par', store=True, currency_field='currency_id')
    costo_docena = fields.Monetary(string='Costo / Docena', compute='_compute_costo_par', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='costo_id.currency_id')

    @api.depends('cantidad', 'precio_unitario', 'rendimiento_pares')
    def _compute_costo_par(self):
        for line in self:
            divisor = line.rendimiento_pares if line.rendimiento_pares > 0 else 1.0
            line.costo_par = (line.cantidad * line.precio_unitario) / divisor
            line.costo_docena = line.costo_par * 12.0

    @api.onchange('insumo_catalogo_id')
    def _onchange_insumo_catalogo_id(self):
        if self.insumo_catalogo_id:
            self.nombre = self.insumo_catalogo_id.name
            self.unidad_medida = self.insumo_catalogo_id.unidad_medida
            self.precio_unitario = self.insumo_catalogo_id.costo_referencia or 0.0


# MODELO HIJO 2: LÍNEA DE LABORES
class CaramiaCostoLaborLine(models.Model):
    _name = 'caramia.costo.labor.line'
    _description = 'Línea de Labores para Cotización'

    costo_id = fields.Many2one('caramia.costo', string='Cotización', ondelete='cascade')
    tipo_labor_id = fields.Many2one('cara.mia.tipo.labor', string='Labor / Proceso', required=True)
    costo_par = fields.Monetary(string='Costo / Par', currency_field='currency_id', required=True)
    costo_docena = fields.Monetary(string='Costo / Docena', compute='_compute_costo_docena', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='costo_id.currency_id')

    @api.depends('costo_par')
    def _compute_costo_docena(self):
        for line in self:
            line.costo_docena = line.costo_par * 12.0