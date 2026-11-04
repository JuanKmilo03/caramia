from odoo import models, fields, api

class CaramiaAgentKnowledge(models.Model):
    _name = 'caramia.agent.knowledge'
    _description = 'Conocimiento para RAG del agente IA'
    _order = 'id desc'

    name = fields.Char(string='Titulo', required=True)
    content = fields.Text(string='Contenido', required=True)
    tags = fields.Char(string='Etiquetas')

class CaramiaAgentCorrection(models.Model):
    _name = 'caramia.agent.correction'
    _description = 'Correcciones/feedback del agente IA'
    _order = 'create_date desc'

    pregunta = fields.Text(string='Pregunta del usuario')
    correccion = fields.Text(string='Correccion', required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.uid)