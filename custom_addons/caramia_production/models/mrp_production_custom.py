from odoo import models, fields, api

class MrpProductionCustom(models.Model):
    _inherit = 'mrp.production'

    shoe_reference_id = fields.Many2one('caramia.shoe.reference', string='Referencia de Calzado')
    caramia_client_id = fields.Many2one(
        'res.partner', string='Cliente',
        domain="[('is_caramia_client', '=', True)]",
        index=True,
    )
    barcode_labor = fields.Char(string='Código de Barras para Escaneo de Labor')
    pairs_count = fields.Integer(string='Total Pares a Fabricar', default=12)
    shoe_last = fields.Char(string='Horma')
    sole_specification = fields.Char(string='Suela / especificación')
    technical_notes = fields.Text(string='Otras especificaciones técnicas')
    size_line_ids = fields.One2many(
        'caramia.production.size.line', 'production_id', string='Cantidades por talla'
    )
    total_pairs_by_size = fields.Integer(
        string='Total pares por tallas', compute='_compute_total_pairs_by_size', store=True
    )

    @api.depends('size_line_ids.pairs_qty')
    def _compute_total_pairs_by_size(self):
        for production in self:
            production.total_pairs_by_size = sum(production.size_line_ids.mapped('pairs_qty'))


class CaramiaProductionSizeLine(models.Model):
    _name = 'caramia.production.size.line'
    _description = 'Cantidad por talla en orden de producción'
    _order = 'size'

    production_id = fields.Many2one(
        'mrp.production', string='Orden de producción', required=True, ondelete='cascade'
    )
    size = fields.Char(string='Talla', required=True)
    pairs_qty = fields.Integer(string='Pares', required=True, default=0)

    _sql_constraints = [
        ('caramia_production_size_unique', 'unique(production_id, size)',
         'Cada talla solo puede registrarse una vez por orden.'),
        ('caramia_production_size_positive', 'CHECK(pairs_qty >= 0)',
         'La cantidad de pares no puede ser negativa.'),
    ]


class ResPartnerProductionHistory(models.Model):
    _inherit = 'res.partner'

    production_order_ids = fields.One2many(
        'mrp.production', 'caramia_client_id', string='Órdenes de producción'
    )
