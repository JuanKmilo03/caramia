from odoo import models, fields, api

class CaramiaProduction(models.Model):
    _name = 'caramia.production'
    _description = 'Orden de Producción'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Orden / Lote', required=True, copy=False, readonly=True, default='Nuevo', tracking=True)
    description = fields.Text(string='Descripción')
    date = fields.Date(string='Fecha de Creación', default=fields.Date.today)
    date_done = fields.Datetime(string='Fecha de Finalización', readonly=True)
    active = fields.Boolean(string='Activo', default=True)

    # Relaciones y datos del producto
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    product_id = fields.Many2one('product.product', string='Referencia / Producto', required=True, tracking=True)
    color = fields.Char(string='Color')
    material = fields.Char(string='Material')
    sello = fields.Char(string='Sello / Marca')
    factura_nro = fields.Char(string='Factura N°')

    # Curva completa de tallas (21 a 40)
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

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Intenta autocompletar atributos si están definidos en el producto"""
        if self.product_id:
            self.color = getattr(self.product_id, 'color', False) or self.color
            self.material = getattr(self.product_id, 'material', False) or self.material

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('caramia.production.number') or 'Nuevo'
        return super().create(vals_list)

    def action_set_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_set_done(self):
        self.write({
            'state': 'done',
            'date_done': fields.Datetime.now()
        })

    def action_set_draft(self):
        self.write({
            'state': 'draft',
            'date_done': False
        })

    def action_download_pdf(self):
        """Ejecuta la descarga directa del reporte PDF con tiquetes de producción"""
        return self.env.ref('caramia_production.action_report_caramia_production').report_action(self)