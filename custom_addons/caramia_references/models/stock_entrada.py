from odoo import models, fields, api

class CaramiaStockEntrada(models.Model):
    _name = 'cara.mia.stock.entrada'
    _description = 'Entradas de Stock de Insumos'
    _order = 'fecha desc, id desc'

    insumo_id = fields.Many2one(
        'cara.mia.insumo.catalogo', 
        string='Insumo del Catálogo', 
        required=True, 
        ondelete='cascade'
    )

    tipo_componente_id = fields.Many2one(
        'cara.mia.tipo.componente',
        string='Tipo de Componente',
        required=True
    )  
    cantidad = fields.Float(string='Cantidad a Ingresar', required=True)
    fecha = fields.Date(string='Fecha de Entrada', default=fields.Date.context_today, required=True)
    referencia_factura = fields.Char(string='Nº Factura / Remisión')
    observaciones = fields.Text(string='Notas')
    
