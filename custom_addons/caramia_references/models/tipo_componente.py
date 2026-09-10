from odoo import models, fields, api

class TipoComponente(models.Model):
    _name = 'cara.mia.tipo.componente'
    _description = 'Tipo de Componente de Calzado'

    name = fields.Char(string='Nombre del Tipo', required=True)