from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..models.cuenta_cobro import METODOS_PAGO


class CaramiaCuentaAnularWizard(models.TransientModel):
    _name = 'cara.mia.cuenta.anular.wizard'
    _description = 'Anular Cuenta de Cobro'

    cuenta_id = fields.Many2one('cara.mia.cuenta.cobro', string='Cuenta de Cobro', required=True)    
    currency_id = fields.Many2one(related='cuenta_id.currency_id')
    total_abonado = fields.Monetary(related='cuenta_id.total_abonado', string='Abonado hasta ahora')
    motivo = fields.Text(string='Motivo de la anulación', required=True)

    def action_confirmar(self):
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
        return {'type': 'ir.actions.act_window_close'}


class CaramiaPagoWizard(models.TransientModel):
    _name = 'cara.mia.pago.wizard'
    _description = 'Registrar Pago a una o varias Facturas'

    cliente_id = fields.Many2one('cara.mia.cliente', string='Cliente', required=True)
    cuenta_id = fields.Many2one('cara.mia.cuenta.cobro', string='Cuenta prioritaria')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    fecha = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    monto = fields.Monetary(string='Monto recibido')
    metodo = fields.Selection(METODOS_PAGO, string='Forma de Pago', default='efectivo', required=True)
    referencia = fields.Char(string='N° Comprobante')
    observacion = fields.Char(string='Observación')
    linea_ids = fields.One2many('cara.mia.pago.wizard.linea', 'wizard_id', string='Facturas')
    saldo_cliente = fields.Monetary(string='Saldo del cliente', compute='_compute_totales')
    total_aplicado = fields.Monetary(string='Total aplicado', compute='_compute_totales')

    @api.depends('linea_ids.saldo_pendiente', 'linea_ids.monto_aplicar')
    def _compute_totales(self):
        for rec in self:
            rec.saldo_cliente = sum(rec.linea_ids.mapped('saldo_pendiente'))
            rec.total_aplicado = sum(rec.linea_ids.mapped('monto_aplicar'))

    @api.model
    def _lineas_vals(self, cliente_id, cuenta_id=False):
        """Cuentas abiertas del cliente: la prioritaria primero, luego por vencimiento."""
        cuentas = self.env['cara.mia.cuenta.cobro'].search([
            ('cliente_id', '=', cliente_id),
            ('estado', 'in', ('vigente', 'vencida')),
        ], order='fecha_vencimiento, id')
        prioritaria = cuentas.filtered(lambda c: c.id == cuenta_id)
        cuentas = prioritaria | (cuentas - prioritaria)
        return [(0, 0, {'cuenta_id': c.id}) for c in cuentas]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get('cliente_id') and 'linea_ids' in fields_list:
            res['linea_ids'] = self._lineas_vals(res['cliente_id'], res.get('cuenta_id'))
        return res

    @api.onchange('cliente_id')
    def _onchange_cliente_id(self):
        self.linea_ids = [(5, 0, 0)]
        if self.cliente_id:
            self.linea_ids = self._lineas_vals(self.cliente_id.id, self.cuenta_id.id)

    @api.onchange('monto')
    def _onchange_monto(self):
        """Reparte el monto recibido entre las facturas, de la más antigua a la más nueva."""
        restante = self.monto or 0.0
        for linea in self.linea_ids:
            aplicar = min(restante, linea.saldo_pendiente)
            linea.monto_aplicar = aplicar
            restante -= aplicar

    def action_registrar(self):
        self.ensure_one()
        lineas = self.linea_ids.filtered(lambda l: l.monto_aplicar > 0)
        if not lineas:
            raise UserError("Indique el monto a aplicar en al menos una factura.")
        if self.monto and self.currency_id.compare_amounts(self.total_aplicado, self.monto) != 0:
            raise UserError(
                "El total aplicado a las facturas (%s) no coincide con el monto recibido (%s)."
                % (self.total_aplicado, self.monto))
        for linea in lineas:
            if self.currency_id.compare_amounts(linea.monto_aplicar, linea.saldo_pendiente) > 0:
                raise UserError(
                    "El monto aplicado a la factura %s supera su saldo (%s)."
                    % (linea.cuenta_id.name, linea.saldo_pendiente))
        self.env['cara.mia.cuenta.cobro.pago'].create([{
            'cuenta_id': linea.cuenta_id.id,
            'fecha': self.fecha,
            'monto': linea.monto_aplicar,
            'metodo': self.metodo,
            'referencia': self.referencia,
            'observacion': self.observacion,
        } for linea in lineas])
        return {'type': 'ir.actions.act_window_close'}


class CaramiaPagoWizardLinea(models.TransientModel):
    _name = 'cara.mia.pago.wizard.linea'
    _description = 'Línea del asistente de pagos'

    wizard_id = fields.Many2one('cara.mia.pago.wizard', ondelete='cascade')
    cuenta_id = fields.Many2one('cara.mia.cuenta.cobro', string='Factura', required=True)    
    currency_id = fields.Many2one(related='cuenta_id.currency_id')
    fecha_vencimiento = fields.Date(related='cuenta_id.fecha_vencimiento', string='Vence')
    estado = fields.Selection(related='cuenta_id.estado', string='Estado')
    saldo_pendiente = fields.Monetary(related='cuenta_id.saldo_pendiente', string='Saldo')
    monto_aplicar = fields.Monetary(string='Aplicar', default=0.0)