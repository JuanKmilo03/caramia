from odoo import models


class CaramiaProductionCompra(models.Model):
    _inherit = 'cara.mia.produccion'

    def action_imprimir_lista_compras(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lista de Compras',
            'res_model': 'caramia.lista.compras.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
            },
        }