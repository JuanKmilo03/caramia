# -*- coding: utf-8 -*-
from odoo import models, fields


class ListaComprasWizard(models.TransientModel):
    _name = 'caramia.lista.compras.wizard'
    _description = 'Vista Previa Lista de Compras'

    production_id = fields.Many2one(
        'cara.mia.produccion',
        string='Orden de Producción',
        required=True,
        readonly=True
    )
    observaciones = fields.Html(
        string='Observaciones',
        help='Texto e imágenes que se incluirán en la orden de compra impresa'
    )

    name = fields.Char(related='production_id.name', readonly=True)
    customer_name = fields.Char(
        related='production_id.cliente_id.nombre_cliente',
        readonly=True,
        string='Cliente'
    )
    
    referencia_nombre = fields.Char(
        related='production_id.referencia_id.nombre_modelo',
        readonly=True,
        string='Modelo'
    )
    total_pares = fields.Integer(
        related='production_id.total_pares',
        readonly=True,
        string='Total Pares'
    )

    def action_imprimir(self):
        self.ensure_one()
        return self.env.ref(
            'caramia_production.action_report_lista_compras_production'
        ).report_action(self)