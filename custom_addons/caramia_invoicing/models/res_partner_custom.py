from odoo import models, fields

class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    is_caramia_client = fields.Boolean(
        string='Es Cliente Cara Mia',
        default=False,
        help='Indica que el contacto se gestiona desde el módulo de Clientes de Cara Mia.',
    )
    client_type = fields.Selection([
        ('wholesaler', 'Mayorista'),
        ('retailer', 'Boutique / Tienda'),
        ('distributor', 'Distribuidor Nacional'),
        ('final', 'Cliente Final'),
    ], string='Tipo de Cliente', default='wholesaler')
    
    credit_limit_custom = fields.Float(string='Límite de Crédito ($)', default=0.0)
    preferred_transport = fields.Char(string='Transportadora Preferida')
    commercial_notes = fields.Text(string='Preferencias del Cliente')
