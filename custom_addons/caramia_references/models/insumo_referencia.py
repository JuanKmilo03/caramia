from odoo import models, fields, api

class InsumoReferencia(models.Model):
    _name = 'cara.mia.insumo.referencia'
    _description = 'Insumo de la Ficha Técnica de Calzado'

    referencia_id = fields.Many2one(
        'cara.mia.referencia',
        string='Referencia de Calzado',
        required=True,
        ondelete='cascade'
    )
    insumo_catalogo_id = fields.Many2one(
        'cara.mia.insumo.catalogo',
        string='Material / Insumo',
        required=True
    )
    tipo_componente = fields.Selection(
        related='insumo_catalogo_id.tipo_componente',
        string='Tipo',
        readonly=True
    )
    cantidad = fields.Float(string='Cantidad Requerida', default=1.0)
    unidad_medida = fields.Selection(
        related='insumo_catalogo_id.unidad_medida',
        string='Unidad',
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    costo_estimado = fields.Monetary(
        string='Costo Estimado',
        currency_field='currency_id'
    )

    @api.onchange('insumo_catalogo_id', 'cantidad')
    def _onchange_calcular_costo(self):
        for rec in self:
            if rec.insumo_catalogo_id and rec.cantidad:
                rec.costo_estimado = rec.insumo_catalogo_id.costo_referencia * rec.cantidad