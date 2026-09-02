from odoo import models, fields, api

class CaramiaCustomer(models.Model):
    _name = 'caramia.customer'
    _description = 'Cliente Caramia'
    _order = 'client_code desc, id desc'

    name = fields.Char(string='Nombre / Razón Social', required=True)
    client_code = fields.Char(string='ID Cliente', required=True, copy=False, readonly=True, default='Nuevo')
    phone = fields.Char(string='Teléfono')
    address = fields.Text(string='Dirección')
    sello = fields.Char(string='Sello / Marca')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('client_code', 'Nuevo') == 'Nuevo':
                vals['client_code'] = self.env['ir.sequence'].next_by_code('caramia.client.sequence') or 'Nuevo'
        return super().create(vals_list)