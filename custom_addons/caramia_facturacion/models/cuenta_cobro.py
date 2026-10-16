from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class CaramiaCuentaCobro(models.Model):
    _name = 'cara.mia.cuenta.cobro'
    _description = 'Cuenta de Cobro / Cartera'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_vencimiento asc, id desc'

    name = fields.Char(string='N° Cuenta', required=True, copy=False, readonly=True, default='Nuevo', tracking=True)
    factura_id = fields.Many2one('cara.mia.facturacion', string='Factura Asociada', required=True, readonly=True, ondelete='cascade', tracking=True)
    cliente_id = fields.Many2one('cara.mia.cliente', string='Cliente', required=True, readonly=True, tracking=True)
    
    fecha_emision = fields.Date(string='Fecha Emisión', related='factura_id.fecha_facturacion', store=True, readonly=True)
    fecha_vencimiento = fields.Date(string='Fecha Vencimiento', required=True, tracking=True)
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    monto_total = fields.Monetary(string='Total Factura', required=True, readonly=True, tracking=True)
    total_abonado = fields.Monetary(string='Total Abono', compute='_compute_montos', store=True, tracking=True)
    saldo_pendiente = fields.Monetary(string='Saldo', compute='_compute_montos', store=True, tracking=True)

    pago_linea_ids = fields.One2many('cara.mia.pago.linea', 'cuenta_cobro_id', string='Historial de Pagos / Abonos')
    observaciones = fields.Text(string='Observaciones')
    motivo_anulacion = fields.Text(string='Motivo de Anulación', readonly=True, tracking=True)
    
    estado = fields.Selection([
        ('vigente', 'Vigente'),
        ('vencida', 'Vencida'),
        ('saldada', 'Saldada'),
        ('anulada', 'Anulada')
    ], string='Estado', compute='_compute_estado', store=True, default='vigente', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('cara.mia.cuenta.cobro.seq') or 'CC-' + str(fields.Date.today())
        return super().create(vals_list)

    @api.depends('pago_linea_ids.monto_pago', 'monto_total')
    def _compute_montos(self):
        for rec in self:
            abonado = sum(pago.monto_pago for pago in rec.pago_linea_ids if pago.state == 'confirmado')
            rec.total_abonado = abonado
            rec.saldo_pendiente = max(0.0, rec.monto_total - abonado)

    @api.depends('saldo_pendiente', 'fecha_vencimiento', 'estado')
    def _compute_estado(self):
        hoy = date.today()
        for rec in self:
            if rec.estado == 'anulada':
                continue
            if rec.saldo_pendiente <= 0.0 and rec.monto_total > 0:
                rec.estado = 'saldada'
                if rec.factura_id and rec.factura_id.estado != 'pagada':
                    rec.factura_id.write({'estado': 'pagada'})
            elif rec.fecha_vencimiento and rec.fecha_vencimiento < hoy:
                rec.estado = 'vencida'
            else:
                rec.estado = 'vigente'
                if rec.factura_id and rec.factura_id.estado == 'pagada' and rec.saldo_pendiente > 0:
                    rec.factura_id.write({'estado': 'emitida'})

    def action_registrar_pago_wizard(self):
        self.ensure_one()
        if self.estado in ['saldada', 'anulada']:
            raise ValidationError("No se pueden registrar pagos en una cuenta saldada o anulada.")
        return {
            'name': 'Registrar Pago / Abono',
            'type': 'ir.actions.act_window',
            'res_model': 'cara.mia.pago.linea',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_cuenta_cobro_id': self.id,
                'default_monto_pago': self.saldo_pendiente,
            }
        }

    def action_anular_cuenta(self):
        self.ensure_one()
        return {
            'name': 'Anular Cuenta de Cobro',
            'type': 'ir.actions.act_window',
            'res_model': 'cara.mia.cuenta.anular.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cuenta_id': self.id}
        }


class CaramiaCarteraDashboard(models.TransientModel):
    _name = 'cara.mia.cartera.dashboard'
    _description = 'Dashboard de Cuentas por Cobrar'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    total_facturado_global = fields.Monetary(string='TOTAL FACTURA', compute='_compute_totales_globales')
    total_abonado_global = fields.Monetary(string='TOTAL ABONO', compute='_compute_totales_globales')
    saldo_pendiente_global = fields.Monetary(string='SALDO GENERAL', compute='_compute_totales_globales')

    def _compute_totales_globales(self):
        cuentas = self.env['cara.mia.cuenta.cobro'].search([('estado', 'in', ['vigente', 'vencida'])])
        facturado = sum(c.monto_total for c in cuentas)
        abonado = sum(c.total_abonado for c in cuentas)
        saldo = sum(c.saldo_pendiente for c in cuentas)
        for rec in self:
            rec.total_facturado_global = facturado
            rec.total_abonado_global = abonado
            rec.saldo_pendiente_global = saldo

class CaramiaPagoLinea(models.Model):
    _name = 'cara.mia.pago.linea'
    _description = 'Línea de Pago / Abono'

    cuenta_cobro_id = fields.Many2one('cara.mia.cuenta.cobro', string='Cuenta de Cobro', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='cuenta_cobro_id.currency_id')
    fecha_pago = fields.Date(string='Fecha de Pago', default=fields.Date.context_today, required=True)
    monto_pago = fields.Monetary(string='Monto Abono', required=True)
    metodo_pago = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('consignacion', 'Consignación'),
        ('otro', 'Otro')
    ], string='Método de Pago', default='efectivo', required=True)
    referencia_pago = fields.Char(string='Comprobante / Referencia')
    state = fields.Selection([('confirmado', 'Confirmado')], default='confirmado', string='Estado')

    @api.constrains('monto_pago')
    def _check_monto_pago(self):
        for rec in self:
            if rec.monto_pago <= 0:
                raise ValidationError("El monto del abono debe ser mayor a cero.")
            if rec.monto_pago > rec.cuenta_cobro_id.saldo_pendiente:
                raise ValidationError(f"El abono ({rec.monto_pago}) supera el saldo pendiente de la cuenta ({rec.cuenta_cobro_id.saldo_pendiente}).")


# VISTA RESUMEN CONSOLIDADO POR CLIENTE (Como en tu imagen)
class CaramiaClienteCarteraResumen(models.Model):
    _name = 'cara.mia.cliente.cartera.resumen'
    _description = 'Resumen de Cuentas por Cobrar por Cliente'
    _auto = False

    cliente_id = fields.Many2one('cara.mia.cliente', string='Cliente', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    monto_total = fields.Monetary(string='Total Factura', readonly=True)
    total_abonado = fields.Monetary(string='Total Abono', readonly=True)
    saldo_pendiente = fields.Monetary(string='Saldo', readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW cara_mia_cliente_cartera_resumen AS (
                SELECT
                    cc.cliente_id AS id,
                    cc.cliente_id AS cliente_id,
                    cc.currency_id AS currency_id,
                    COALESCE(SUM(cc.monto_total), 0.0) AS monto_total,
                    COALESCE(SUM(cc.total_abonado), 0.0) AS total_abonado,
                    COALESCE(SUM(cc.saldo_pendiente), 0.0) AS saldo_pendiente
                FROM cara_mia_cuenta_cobro cc
                WHERE cc.estado IN ('vigente', 'vencida')
                GROUP BY cc.cliente_id, cc.currency_id
            )
        """)