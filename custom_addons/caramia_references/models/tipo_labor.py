from odoo import models, fields, api
from odoo.exceptions import ValidationError
import unicodedata

class TipoLabor(models.Model):
    _name = 'cara.mia.tipo.labor'
    _description = 'Tipos de Labor'

    name = fields.Char(string='Nombre de la Labor', required=True)
    tarifa_normal = fields.Monetary(string='Tarifa Normal', currency_field='currency_id')
    tarifa_especial = fields.Monetary(string='Tarifa Especial / Compleja', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    def _normalizar_texto(self, texto):
        """Remueve tildes, espacios extras y pasa a minúsculas para comparar de forma estricta"""
        if not texto:
            return ""
        # Quita espacios sobrantes y estandariza a minúsculas
        texto = texto.strip().lower()
        # Remueve acentos y marcas diacríticas (ej: ó -> o)
        nfkd_form = unicodedata.normalize('NFKD', texto)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                nombre_original = vals['name'].strip()
                vals['name'] = nombre_original.capitalize() # Mantiene buena presentación visual
                
                nombre_normalizado = self._normalizar_texto(nombre_original)
                
                # Comparamos contra todos los registros existentes normalizando sus nombres
                todos_registros = self.search([])
                for reg in todos_registros:
                    if self._normalizar_texto(reg.name) == nombre_normalizado:
                        raise ValidationError(f'¡Ya existe una labor registrada con un nombre similar ("{reg.name}")!')
                        
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            nombre_original = vals['name'].strip()
            vals['name'] = nombre_original.capitalize()
            nombre_normalizado = self._normalizar_texto(nombre_original)
            
            todos_registros = self.search([('id', 'not in', self.ids)])
            for reg in todos_registros:
                if self._normalizar_texto(reg.name) == nombre_normalizado:
                    raise ValidationError(f'¡Ya existe otra labor registrada con un nombre similar ("{reg.name}")!')
                    
        return super().write(vals)