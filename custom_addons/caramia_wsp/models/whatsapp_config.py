from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests

class CaramiaWhatsappConfig(models.Model):
    _name = 'cara.mia.whatsapp.config'
    _description = 'Configuración de Gateway de WhatsApp'
    _rec_name = 'name'

    name = fields.Char(string='Nombre del Proveedor', required=True, default='Z-API / Evolution')
    
    proveedor = fields.Selection([
        ('zapi', 'Z-API'),
        ('evolution', 'Evolution API'),
        ('custom', 'Genérico / Otro')
    ], string='Proveedor de API', default='zapi', required=True)

    api_url = fields.Char(string='URL del Endpoint', required=True, help='Ej: https://api.z-api.io/instances/... o https://tu-evolution.com/message/sendText')
    api_token = fields.Char(string='Token de Acceso / API Key', required=True)
    activo = fields.Boolean(string='Usar esta Configuración', default=True)

    @api.model
    def get_active_config(self):
        config = self.search([('activo', '=', True)], limit=1)
        if not config:
            raise ValidationError("No hay ninguna configuración de WhatsApp activa. Diríjase a Facturación > Configuración WhatsApp.")
        return config

    def enviar_mensaje(self, telefono, mensaje):
        self.ensure_one()
        tel_limpio = ''.join(filter(str.isdigit, telefono))

        if self.proveedor == 'zapi':
            headers = {"Content-Type": "application/json", "Client-Token": self.api_token}
            payload = {"phone": tel_limpio, "message": mensaje}
        elif self.proveedor == 'evolution':
            headers = {"Content-Type": "application/json", "apikey": self.api_token}
            payload = {"number": tel_limpio, "text": mensaje}
        else:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_token}"}
            payload = {"to": tel_limpio, "body": mensaje}

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=15)
            if response.status_code in [200, 201]:
                return True
            else:
                raise ValidationError(f"Error devuelto por la API ({self.proveedor}): {response.text}")
        except Exception as e:
            raise ValidationError(f"No se pudo conectar con el servidor de WhatsApp: {str(e)}")