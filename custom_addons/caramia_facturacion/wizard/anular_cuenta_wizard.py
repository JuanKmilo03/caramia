from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CaramiaCuentaAnularWizard(models.TransientModel):
    _name = 'cara.mia.cuenta.anular.wizard'
    _description = 'Anular Cuenta de Cobro'

    cuenta_id = fields.Many2one('cara.mia.cuenta.cobro', string='Cuenta de Cobro', required=True)
    currency_id = fields.Many2one(related='cuenta_id.currency_id')
    total_abonado = fields.Monetary(related='cuenta_id.total_abonado', string='Abonado hasta ahora')
    motivo = fields.Text(string='Motivo de la anulación', required=True)

    def action_confirmar_anulacion(self):
        self.ensure_one()
        cuenta = self.cuenta_id
        if cuenta.estado not in ('vigente', 'vencida'):
            raise UserError("Solo se pueden anular cuentas vigentes o vencidas.")
        motivo = (self.motivo or '').strip()
        if not motivo:
            raise ValidationError("Debe indicar el motivo de la anulación.")
        cuenta.write({
            'estado': 'anulada',
            'motivo_anulacion': motivo,
            'fecha_anulacion': fields.Datetime.now(),
            'usuario_anulacion_id': self.env.uid,
        })
        factura = cuenta.factura_id
        if factura:
            factura.write({'estado': 'anulada'})
            factura.linea_ids.produccion_id.write({'factura_id': False})
        return {'type': 'ir.actions.act_window_close'}