from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    caramia_dias_borrador = fields.Integer(
        string='Aviso de orden en borrador (días)',
        config_parameter='caramia_production.dias_borrador',
        default=3,
        help='Días que puede permanecer una orden en borrador antes de marcarse '
             'como estancada.',
    )
    caramia_dias_etapa = fields.Integer(
        string='Aviso de labor sin avance (días)',
        config_parameter='caramia_production.dias_etapa',
        default=7,
        help='Días sin avance en la labor actual antes de marcarse como estancada.',
    )
