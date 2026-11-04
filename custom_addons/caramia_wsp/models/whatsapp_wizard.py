from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class CaramiaWhatsappWizard(models.TransientModel):
    _name = 'cara.mia.whatsapp.wizard'
    _description = 'Asistente de Envío de WhatsApp Masivo'

    linea_ids = fields.One2many(
        'cara.mia.whatsapp.wizard.linea', 
        'wizard_id', 
        string='Cuentas Pendientes',
        compute='_compute_linea_ids',
        store=False,
        readonly=False
    )

    @api.depends()
    def _compute_linea_ids(self):
        # Buscamos todas las cuentas pendientes
        cuentas = self.env['cara.mia.cuenta.cobro'].search([('estado', 'not in', ('saldada', 'anulada'))])
        
        for wizard in self:
            lineas_vals = []
            for cuenta in cuentas:
                cliente = cuenta.cliente_id
                telefono = ''
                if cliente:
                    telefono = getattr(cliente, 'phone', '') or getattr(cliente, 'mobile', '') or ''
                
                lineas_vals.append((0, 0, {
                    'cuenta_id': cuenta.id,
                    'cliente_id': cliente.id if cliente else False,
                    'telefono': telefono or '',
                    'fecha_vencimiento': cuenta.fecha_vencimiento or fields.Date.today(),
                    'saldo_pendiente': cuenta.saldo_pendiente or 0.0,
                    'currency_id': cuenta.currency_id.id if cuenta.currency_id else False,
                    'enviar': True,
                }))
            wizard.linea_ids = lineas_vals

    def action_enviar_recordatorios(self):
        self.ensure_one()
        config = self.env['cara.mia.whatsapp.config'].get_active_config()

        enviados = 0
        for linea in self.linea_ids:
            if linea.enviar:
                if not linea.telefono:
                    raise ValidationError(f"El cliente {linea.cliente_id.name} no tiene número de teléfono registrado.")
                
                # Formato de mensaje corregido y limpio
                saldo_formateado = f"{linea.saldo_pendiente:,.2f}"
                factura_nombre = linea.cuenta_id.factura_id.name if linea.cuenta_id.factura_id else 'N/A'
                
                mensaje = (
                    f"Estimado/a *{linea.cliente_id.name}*,\n\n"
                    f"Le recordamos desde *Calzado Cara Mía* que tiene un saldo pendiente de "
                    f"*{saldo_formateado}* en la factura *{factura_nombre}* "
                    f"con fecha de vencimiento *{linea.fecha_vencimiento}*.\n\n"
                    f"Agradecemos su gestión de pago. ¡Feliz día!"
                )
                
                config.enviar_mensaje(linea.telefono, mensaje)
                enviados += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '¡Envío Exitoso!',
                'message': f'Se han enviado {enviados} recordatorios por WhatsApp correctamente.',
                'type': 'success',
                'sticky': False,
            }
        }


class CaramiaWhatsappWizardLinea(models.TransientModel):
    _name = 'cara.mia.whatsapp.wizard.linea'
    _description = 'Línea del Asistente de WhatsApp'

    wizard_id = fields.Many2one('cara.mia.whatsapp.wizard', ondelete='cascade')
    enviar = fields.Boolean(string='Enviar', default=True)
    cuenta_id = fields.Many2one('cara.mia.cuenta.cobro', string='Cuenta de Cobro', readonly=True)
    cliente_id = fields.Many2one('res.partner', string='Cliente', readonly=True)  # Ajustado a res.partner o tu modelo de cliente
    telefono = fields.Char(string='Teléfono', readonly=True)
    saldo_pendiente = fields.Monetary(string='Saldo Pendiente', readonly=True)
    currency_id = fields.Many2one('res.currency')
    fecha_vencimiento = fields.Date(string='Vencimiento', readonly=True)