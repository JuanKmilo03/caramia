from odoo import models, fields, api

class CaramiaCustomer(models.Model):
    _name = 'cara.mia.cliente'
    _description = 'Cliente Caramia'
    _rec_name = 'nombre_cliente'

    nombre_cliente = fields.Char(string='Nombre / Razón Social', required=True)
    cliente_id = fields.Char(string='ID Cliente', required=True, copy=False, readonly=True, default='Nuevo')
    telefono_cliente = fields.Char(string='Teléfono')
    direccion = fields.Text(string='Dirección')
    sello = fields.Char(string='Sello / Marca')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('cliente_id', 'Nuevo') == 'Nuevo':
                vals['cliente_id'] = self.env['ir.sequence'].next_by_code('caramia.client.sequence') or 'Nuevo'
        return super().create(vals_list)