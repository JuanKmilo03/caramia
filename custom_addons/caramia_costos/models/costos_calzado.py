from odoo import models, fields, api
from odoo.exceptions import UserError


class CaramiaCosto(models.Model):
    _name = 'caramia.costo'
    _description = 'Cotización y Hoja de Costos de Calzado'
    _order = 'name desc'

    name = fields.Char(
        string='Nº Cotización',
        required=True,
        readonly=True,
        default='Nuevo',
        copy=False
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    fecha = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        required=True
    )
    cliente_id = fields.Many2one(
        'cara.mia.cliente',
        string='Cliente',
        tracking=True
    )
    referencia_id = fields.Many2one(
        'cara.mia.referencia',
        string='Modelo',
        required=False,
        tracking=True,
        domain="[('estado', '=', 'activo')]"
    )
    
    nombre_modelo = fields.Char(string='O escribe un modelo nuevo')
    
    observaciones = fields.Text(string='Notas / Observaciones')

    tipo_lote = fields.Selection([
        ('12', 'Docena (12)'),
        ('24', 'Doble Docena (24)'),
        ('custom', 'Personalizado'),
    ], string='Tipo de Lote', default='12', required=True)

    cantidad_lote = fields.Integer(
        string='Cantidad del Lote',
        default=12,
        help='Número de pares del lote para calcular costos totales'
    )

    @api.onchange('tipo_lote')
    def _onchange_tipo_lote(self):
        if self.tipo_lote == '12':
            self.cantidad_lote = 12
        elif self.tipo_lote == '24':
            self.cantidad_lote = 24

    material_ids = fields.One2many(
        'caramia.costo.material.line',
        'costo_id',
        string='Materiales e Insumos'
    )
    labor_ids = fields.One2many(
        'caramia.costo.labor.line',
        'costo_id',
        string='Mano de Obra'
    )

    total_materiales_par = fields.Monetary(
        string='Total materiales por par',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    total_labores_par = fields.Monetary(
        string='Total labores por par',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    costo_total_par = fields.Monetary(
        string='Costo total por par',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    costo_total_lote = fields.Monetary(
        string='Costo total por lote',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    precio_venta_par = fields.Monetary(
        string='Precio venta por par',
        currency_field='currency_id',
        tracking=True,
    )
    margen_ganancia = fields.Monetary(
        string='Margen Ganancia',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id',
    )
    precio_venta_lote = fields.Monetary(
        string='Precio Venta Por Lote',
        compute='_compute_totales',
        store=True,
        currency_field='currency_id'
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('production', 'En Producción'),
    ], string='Estado', default='draft', tracking=True)

    production_id = fields.Many2one(
        'cara.mia.produccion',
        string='Orden de Producción',
        readonly=True
    )

    @api.depends(
        'material_ids.costo_par',
        'labor_ids.costo_par',
        'precio_venta_par',
        'cantidad_lote'
    )
    def _compute_totales(self):
        for rec in self:
            lote = rec.cantidad_lote or 1
            rec.total_materiales_par = sum(rec.material_ids.mapped('costo_par'))
            rec.total_labores_par    = sum(rec.labor_ids.mapped('costo_par'))
            rec.costo_total_par      = rec.total_materiales_par + rec.total_labores_par
            rec.costo_total_lote     = rec.costo_total_par * lote
            rec.margen_ganancia      = rec.precio_venta_par - rec.costo_total_par
            rec.precio_venta_lote    = rec.precio_venta_par * lote

    def action_guardar_como_referencia(self):
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Guardar como Referencia',
                'res_model': 'caramia.guardar.referencia.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_costo_id':              self.id,
                    'default_precio_venta_sugerido': self.precio_venta_par,
                    'default_nombre_modelo': (
                        self.referencia_id.nombre_modelo + ' (Copia)'
                        if self.referencia_id else ''
                    ),
                    'default_referencia_a_actualizar_id': self.referencia_id.id,
                },
            }
    def _get_lineas_materiales(self, referencia):
        lote = self.cantidad_lote or 12
        lineas = []
        for insumo_ref in referencia.insumo_ids:
            catalogo = insumo_ref.insumo_catalogo_id
            if not catalogo:
                continue
            # cantidad en referencia está guardada por par → multiplicar por lote
            lineas.append(fields.Command.create({
                'insumo_catalogo_id': catalogo.id,
                'tipo_componente_id': catalogo.tipo_componente_id.id if catalogo.tipo_componente_id else False,
                'unidad_medida': insumo_ref.unidad_medida,
                'cantidad_docena': insumo_ref.cantidad * lote,
                'precio_unitario': catalogo.costo_referencia or 0.0,
            }))
        return lineas

    def _get_lineas_labores(self, referencia):
        """Devuelve lista de Command.create para labores de una referencia."""
        lineas = []
        for labor_ref in referencia.labor_ids:
            if not labor_ref.tipo_labor_id:
                continue
            lineas.append(fields.Command.create({
                'tipo_labor_id': labor_ref.tipo_labor_id.id,
                'costo_par':     labor_ref.tarifa_pago or 0.0,
            }))
        return lineas

    @api.onchange('referencia_id')
    def _onchange_referencia_id(self):
        if not self.referencia_id:
            self.material_ids = [(5, 0, 0)]
            self.labor_ids = [(5, 0, 0)]
            self.precio_venta_par = 0.0
            return

        self.precio_venta_par = self.referencia_id.precio_venta_sugerido or 0.0
        self.material_ids = [(5, 0, 0)] + [
            (0, 0, {
                'insumo_catalogo_id': insumo_ref.insumo_catalogo_id.id,
                'tipo_componente_id': insumo_ref.insumo_catalogo_id.tipo_componente_id.id or False,
                'unidad_medida': insumo_ref.unidad_medida,
                'cantidad_docena': insumo_ref.cantidad * (self.cantidad_lote or 12),
                'precio_unitario': insumo_ref.insumo_catalogo_id.costo_referencia or 0.0,
            })
            for insumo_ref in self.referencia_id.insumo_ids
            if insumo_ref.insumo_catalogo_id
        ]
        self.labor_ids = [(5, 0, 0)] + [
            (0, 0, {
                'tipo_labor_id': l.tipo_labor_id.id,
                'costo_par': l.tarifa_pago or 0.0,
            })
            for l in self.referencia_id.labor_ids
            if l.tipo_labor_id
        ]
    
    def action_actualizar_desde_referencia(self):
        self.ensure_one()
        if not self.referencia_id:
            raise UserError('No hay referencia seleccionada.')

        if self.referencia_id.precio_venta_sugerido:
            self.precio_venta_par = self.referencia_id.precio_venta_sugerido

        for linea in self.material_ids:
            if linea.insumo_catalogo_id:
                linea.precio_unitario = linea.insumo_catalogo_id.costo_referencia or 0.0

        tarifas = {
            l.tipo_labor_id.id: l.tarifa_pago
            for l in self.referencia_id.labor_ids
            if l.tipo_labor_id
        }
        for linea in self.labor_ids:
            if linea.tipo_labor_id.id in tarifas:
                linea.costo_par = tarifas[linea.tipo_labor_id.id]

    def action_borrador(self):
        self.write({'state': 'draft'})
        
    def _crear_orden_produccion(self):
        self.ensure_one()
        ref = self.referencia_id

        labores_vals = []
        for labor_ref in ref.labor_ids:
            if labor_ref.tipo_labor_id:
                labores_vals.append((0, 0, {
                    'tipo_labor_id': labor_ref.tipo_labor_id.id,
                    'tarifa_pago':   labor_ref.tarifa_pago or 0.0,
                }))

        sello = ''
        if hasattr(self.cliente_id, 'sello') and self.cliente_id.sello:
            sello = self.cliente_id.sello

        nueva_op = self.env['cara.mia.produccion'].create({
            'cliente_id':    self.cliente_id.id,
            'referencia_id': ref.id,
            'description': (
                f'Generado desde Cotización {self.name}.\n'
                f'Observaciones: {self.observaciones or ""}'
            ),
            'company_id': self.company_id.id,
            'color':      '',
            'material':   '',
            'sello':      sello,
            'labor_ids':  labores_vals,
        })

        self.write({
            'state': 'production',
            'production_id': nueva_op.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Producción',
            'res_model': 'cara.mia.produccion',
            'res_id': nueva_op.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_pass_to_production(self):
        self.ensure_one()

        if self.production_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'cara.mia.produccion',
                'res_id': self.production_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        if not self.cliente_id:
            raise UserError('Debe seleccionar un Cliente antes de pasar a producción.')

        if not self.referencia_id and self.nombre_modelo:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Guardar modelo como referencia',
                'res_model': 'caramia.guardar.referencia.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_costo_id': self.id,
                    'default_modo': 'nueva',
                    'default_nombre_modelo': self.nombre_modelo,
                    'default_precio_venta_sugerido': self.precio_venta_par,
                    'continuar_a_produccion': True,
                },
            }

        if not self.referencia_id:
            raise UserError(
                'Selecciona un modelo existente o escribe el nombre de un modelo nuevo.'
            )

        return self._crear_orden_produccion()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('caramia.costo.number')
                    or 'Nuevo'
                )
        return super().create(vals_list)