from odoo import models, fields, api

class CaramiaAgentLog(models.Model):
    _name = 'caramia.agent.log'
    _description = 'Log de acciones del agente IA'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.uid)
    accion = fields.Char(string='Accion')
    parametros = fields.Text(string='Parametros')
    resultado = fields.Text(string='Resultado')
    exito = fields.Boolean(string='Exito', default=True)