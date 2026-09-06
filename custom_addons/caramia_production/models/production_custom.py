from odoo import models, fields, api

# Selección estándar de labores de producción
TIPOS_LABOR = [
    ('limpiada', 'Limpiada'),
    ('montada', 'Montada'),
    ('guarnicion', 'Guarnición'),
    ('plantilla', 'Plantilla'),
    ('forrada', 'Forrada'),
    ('corte', 'Corte'),
    ('otro', 'Otra Labor')
]

class CaramiaProduction(models.Model):
    _name = 'caramia.production'
    _description = 'Orden de Producción'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Orden / Lote', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='Nuevo', 
        tracking=True
    )
    description = fields.Text(string='Descripción / Observaciones')
    date = fields.Date(string='Fecha de Creación', default=fields.Date.today)
    date_done = fields.Datetime(string='Fecha de Finalización', readonly=True)
    active = fields.Boolean(string='Activo', default=True)

    # Relaciones principales
    customer_id = fields.Many2one('caramia.customer', string='Cliente', required=True, tracking=True)
    referencia_id = fields.Many2one(
        'cara.mia.referencia', 
        string='Referencia / Modelo', 
        required=True, 
        tracking=True,
        domain="[('estado', '=', 'activo')]",
        ondelete='restrict'
    )

    imagen_zapato = fields.Image(
        related='referencia_id.imagen_zapato', 
        string='Fotografía del Calzado', 
        readonly=True
    )

    # Relación con labores editables propias de esta orden
    labor_ids = fields.One2many(
        'caramia.production.labor', 
        'production_id', 
        string='Labores de la Orden'
    )

    currency_id = fields.Many2one(
        'res.currency', 
        default=lambda self: self.env.company.currency_id, 
        string='Moneda'
    )

    color = fields.Char(string='Color')
    material = fields.Char(string='Material')
    sello = fields.Char(string='Sello / Marca')
    factura_nro = fields.Char(string='Factura N°')

    # Curva de tallas (21 a 40)
    talla_21 = fields.Integer(string='21', default=0)
    talla_22 = fields.Integer(string='22', default=0)
    talla_23 = fields.Integer(string='23', default=0)
    talla_24 = fields.Integer(string='24', default=0)
    talla_25 = fields.Integer(string='25', default=0)
    talla_26 = fields.Integer(string='26', default=0)
    talla_27 = fields.Integer(string='27', default=0)
    talla_28 = fields.Integer(string='28', default=0)
    talla_29 = fields.Integer(string='29', default=0)
    talla_30 = fields.Integer(string='30', default=0)
    talla_31 = fields.Integer(string='31', default=0)
    talla_32 = fields.Integer(string='32', default=0)
    talla_33 = fields.Integer(string='33', default=0)
    talla_34 = fields.Integer(string='34', default=0)
    talla_35 = fields.Integer(string='35', default=0)
    talla_36 = fields.Integer(string='36', default=0)
    talla_37 = fields.Integer(string='37', default=0)
    talla_38 = fields.Integer(string='38', default=0)
    talla_39 = fields.Integer(string='39', default=0)
    talla_40 = fields.Integer(string='40', default=0)

    total_pares = fields.Integer(string='Total Pares', compute='_compute_total_pares', store=True)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Proceso'),
        ('done', 'Finalizado'),
    ], string='Estado', default='draft', tracking=True)

    @api.depends(
        'talla_21', 'talla_22', 'talla_23', 'talla_24', 'talla_25',
        'talla_26', 'talla_27', 'talla_28', 'talla_29', 'talla_30',
        'talla_31', 'talla_32', 'talla_33', 'talla_34', 'talla_35',
        'talla_36', 'talla_37', 'talla_38', 'talla_39', 'talla_40'
    )
    def _compute_total_pares(self):
        for rec in self:
            rec.total_pares = sum([
                rec.talla_21, rec.talla_22, rec.talla_23, rec.talla_24, rec.talla_25,
                rec.talla_26, rec.talla_27, rec.talla_28, rec.talla_29, rec.talla_30,
                rec.talla_31, rec.talla_32, rec.talla_33, rec.talla_34, rec.talla_35,
                rec.talla_36, rec.talla_37, rec.talla_38, rec.talla_39, rec.talla_40
            ])

    @api.onchange('referencia_id')
    def _onchange_referencia_id(self):
        if self.referencia_id:
            if getattr(self.referencia_id, 'descripcion', False) and not self.description:
                self.description = self.referencia_id.descripcion

            # Extrae las tarifas de las labores configuradas en la referencia de zapato
            precios_ref = {lab.tipo_labor: lab.tarifa_pago for lab in self.referencia_id.labor_ids}

            # Carga todas las labores estándar en la orden con su valor o $0.0
            lineas_labores = []
            for code, name in TIPOS_LABOR:
                lineas_labores.append((0, 0, {
                    'tipo_labor': code,
                    'tarifa_pago': precios_ref.get(code, 0.0),
                }))
            
            self.labor_ids = [(5, 0, 0)] + lineas_labores

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id and getattr(self.customer_id, 'sello', False):
            self.sello = self.customer_id.sello

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('caramia.production.number') or 'Nuevo'
        return super().create(vals_list)

    # Métodos invocados por los botones del encabezado en la vista
    def action_set_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_set_done(self):
        self.write({'state': 'done', 'date_done': fields.Datetime.now()})

    def action_set_draft(self):
        self.write({'state': 'draft', 'date_done': False})

    def action_download_pdf(self):
        return self.env.ref('caramia_production.action_report_caramia_production').report_action(self)


class CaramiaProductionLabor(models.Model):
    _name = 'caramia.production.labor'
    _description = 'Labor Editable de Orden de Producción'

    production_id = fields.Many2one('caramia.production', string='Orden de Producción', ondelete='cascade')
    tipo_labor = fields.Selection(TIPOS_LABOR, string='Tipo de Labor', required=True)
    tarifa_pago = fields.Monetary(string='Precio por Par', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='production_id.currency_id')