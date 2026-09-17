from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CaramiaProduction(models.Model):
    _name = 'cara.mia.produccion'
    _description = 'Orden de Producción'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Orden / Lote', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='Nuevo', 
        tracking=True
    )
    descripcion = fields.Text(string='Descripción / Observaciones')
    fecha_creacion = fields.Date(string='Fecha de Creación', default=fields.Date.today)
    fecha_estimada = fields.Date(string='Fecha Estimada de Finalización', readonly=True)
    fecha_finalizacion = fields.Datetime(string='Fecha de Finalización', readonly=True)
    activo = fields.Boolean(string='Activo', default=True)

    # Relaciones principales
    cliente_id = fields.Many2one('cara.mia.cliente', string='Cliente', required=True, tracking=True)
    referencia_id = fields.Many2one(
        'cara.mia.referencia',
        string='Referencia / Modelo',
        required=True,
        tracking=True,
        domain="[('estado', '=', 'activo')]",
        ondelete='restrict'
    )

    imagen_zapato = fields.Image(related='referencia_id.imagen_zapato', string='Fotografía del Calzado', readonly=True)

    # Labores asociadas a esta orden
    labor_ids = fields.One2many(
        'cara.mia.produccion.labor', 
        'produccion_id', 
        string='Labores de la Orden'
    )

    currency_id = fields.Many2one(
        'res.currency', 
        default=lambda self: self.env.company.currency_id, 
        string='Moneda'
    )

    color = fields.Char(string='Color', required=True)
    material = fields.Char(string='Material', required=True)
    sello = fields.Char(string='Sello / Marca', required=True)
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
        ('canceled', 'Cancelado'),
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

    @api.constrains('total_pares')
    def _check_total_pares(self):
        for rec in self:
            if rec.total_pares <= 0:
                raise ValidationError(
                    "Debe ingresar al menos un par de zapatos en alguna de las tallas antes de guardar la orden."
                )

    @api.onchange('referencia_id')
    def _onchange_referencia_id(self):
        self.labor_ids = [(5, 0, 0)]
        if self.referencia_id:
            self.labor_ids = [
                (0, 0, {
                    'tipo_labor_id': labor.tipo_labor_id.id,
                    'tarifa_pago': labor.tarifa_pago or 0.0,
                })
                for labor in self.referencia_id.labor_ids
                if labor.tipo_labor_id
            ]

    @api.onchange('cliente_id')
    def _onchange_cliente_id(self):
        if self.cliente_id and getattr(self.cliente_id, 'sello', False):
            self.sello = self.cliente_id.sello

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('cara.mia.produccion.number') or 'Nuevo'
        return super().create(vals_list)

    def action_set_in_progress(self):
        for rec in self:
            if not rec.labor_ids:
                raise ValidationError("No se puede iniciar una orden de producción sin labores asignadas.")
            rec.write({'state': 'in_progress'})

    def action_set_draft(self):
        for rec in self:
            if getattr(rec, 'registro_trabajo_ids', False):
                raise ValidationError("No puede regresar a Borrador una orden que ya tiene tiquetes o trabajos registrados.")
            rec.write({'state': 'draft', 'fecha_finalizacion': False})

    def action_cancel(self):
        self.write({'state': 'canceled'})

    def action_download_pdf(self):
        return self.env.ref('caramia_production.action_report_caramia_production').report_action(self)


class CaramiaProductionLabor(models.Model):
    _name = 'cara.mia.produccion.labor'
    _description = 'Labor Editable de Orden de Producción'

    produccion_id = fields.Many2one('cara.mia.produccion', string='Orden de Producción', ondelete='cascade')
    tipo_labor_id = fields.Many2one('cara.mia.tipo.labor', string='Labor / Proceso', required=True)    
    tarifa_pago = fields.Monetary(string='Precio por Par', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='produccion_id.currency_id')