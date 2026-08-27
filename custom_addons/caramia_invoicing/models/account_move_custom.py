from odoo import models, fields

class AccountMoveCustom(models.Model):
    _inherit = 'account.move'

    caramia_notes = fields.Text(string='Condiciones Especiales de Entrega y Cobro')
