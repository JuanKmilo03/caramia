from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CaramiaCuentaAnularWizard(models.TransientModel):
    _name = 'cara.mia.cuenta.anular.wizard'
    _description = 'Asistente para Anular Cuenta de Cobro'

    cuenta_id = fields.Many2one('cara.mia.cuenta.cobro', string='Cuenta de Cobro', required=True)
    motivo = fields.Text(string='Motivo de Anulación', required=True)

    def action_confirmar_anulacion(self):
        self.ensure_one()
        if not self.motivo:
            raise ValidationError("Debe detallar el motivo por el cual se anula la cuenta.")
        
        cuenta = self.cuenta_id
        cuenta.write({
            'estado': 'anulada',
            'motivo_anulacion': self.motivo
        })
        
        if cuenta.factura_id:
            cuenta.factura_id.write({'estado': 'anulada'})
            
        return {'type': 'ir.actions.act_window_close'}