import logging
import os
from datetime import timedelta

import requests
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang

_logger = logging.getLogger(__name__)

METODOS_PAGO = [
    ('efectivo', 'Efectivo'),
    ('transferencia', 'Transferencia'),
    ('otro', 'Otro'),
]
ESTADOS_ABIERTOS = ('vigente', 'vencida')


class CaramiaCuentaCobro(models.Model):
    _name = 'cara.mia.cuenta.cobro'
    _description = 'Cuenta de Cobro'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_vencimiento, id'

    factura_id = fields.Many2one('cara.mia.facturacion', string='Factura', required=True,
                                 ondelete='restrict', index=True, tracking=True)
    name = fields.Char(related='factura_id.name', string='N° Factura', store=True)
    cliente_id = fields.Many2one('cara.mia.cliente', related='factura_id.cliente_id',
                                 string='Cliente', store=True, index=True)
    fecha_facturacion = fields.Date(related='factura_id.fecha_facturacion',
                                    string='Fecha de Facturación', store=True)
    fecha_vencimiento = fields.Date(related='factura_id.fecha_vencimiento',
                                    string='Fecha de Vencimiento', store=True)
    forma_pago = fields.Selection(related='factura_id.forma_pago', string='Forma de Pago', store=True)
    currency_id = fields.Many2one(related='factura_id.currency_id', store=True)
    monto_total = fields.Monetary(related='factura_id.total_general', string='Monto', store=True)

    pago_ids = fields.One2many('cara.mia.cuenta.cobro.pago', 'cuenta_id', string='Pagos y Abonos')
    total_abonado = fields.Monetary(string='Abonado', compute='_compute_saldos', store=True)
    saldo_pendiente = fields.Monetary(string='Saldo Pendiente', compute='_compute_saldos', store=True)
    fecha_ultimo_pago = fields.Date(string='Último Pago', compute='_compute_saldos', store=True)
    ordenes_asociadas = fields.Text(string='Órdenes y Referencias',
                                    compute='_compute_ordenes_asociadas', store=True)

    dias_sin_abono = fields.Integer(string='Días sin abono', compute='_compute_alerta', store=True)
    alerta_cobro = fields.Boolean(string='En alerta', compute='_compute_alerta', store=True)
    fecha_ultima_alerta = fields.Date(string='Última alerta enviada', readonly=True, copy=False)
    fecha_aviso_por_vencer = fields.Date(string='Aviso de vencimiento próximo', readonly=True, copy=False)
    fecha_aviso_vencida = fields.Date(string='Último aviso de vencida', readonly=True, copy=False)
    observaciones = fields.Text(string='Observaciones')

    fecha_recordatorio_wa = fields.Date(string='Último recordatorio WhatsApp', readonly=True, copy=False)
    recordatorio_wa_estado = fields.Char(string='Estado recordatorio WhatsApp', readonly=True, copy=False)

    estado = fields.Selection([
        ('vigente', 'Vigente'),
        ('vencida', 'Vencida'),
        ('saldada', 'Saldada'),
        ('anulada', 'Anulada'),
    ], string='Estado', default='vigente', required=True, tracking=True, index=True)

    motivo_anulacion = fields.Text(string='Motivo de Anulación', readonly=True, tracking=True)
    fecha_anulacion = fields.Datetime(string='Fecha de Anulación', readonly=True)
    usuario_anulacion_id = fields.Many2one('res.users', string='Anulada por', readonly=True)


    @api.depends('factura_id.linea_ids.produccion_id', 'factura_id.linea_ids.produccion_id.referencia_id')
    def _compute_ordenes_asociadas(self):
        for rec in self:
            textos = []
            for linea in rec.factura_id.linea_ids.filtered('produccion_id'):
                prod = linea.produccion_id
                ref = prod.referencia_id
                nombre_ref = ref.nombre_modelo or ref.display_name if ref else ''
                texto = prod.display_name
                if nombre_ref:
                    texto += f" - {nombre_ref}"
                textos.append(texto)
            rec.ordenes_asociadas = "\n".join(textos)

    @api.depends('monto_total', 'pago_ids.monto', 'pago_ids.fecha')
    def _compute_saldos(self):
        for rec in self:
            abonado = sum(rec.pago_ids.mapped('monto'))
            rec.total_abonado = abonado
            rec.saldo_pendiente = max(rec.monto_total - abonado, 0.0)
            fechas = [f for f in rec.pago_ids.mapped('fecha') if f]
            rec.fecha_ultimo_pago = max(fechas) if fechas else False

    @api.depends('estado', 'saldo_pendiente', 'fecha_ultimo_pago', 'fecha_facturacion')
    def _compute_alerta(self):
        """Entra en alerta una cuenta vigente con N días sin abonos
        (desde el último abono, o desde la facturación si no ha abonado)."""
        limite = int(self.env['ir.config_parameter'].sudo().get_param(
            'caramia_facturacion.dias_alerta_sin_abono', 15))
        hoy = fields.Date.context_today(self)
        for rec in self:
            base = rec.fecha_ultimo_pago or rec.fecha_facturacion
            abierta = rec.estado in ESTADOS_ABIERTOS
            rec.dias_sin_abono = (hoy - base).days if abierta and base else 0
            rec.alerta_cobro = rec.estado == 'vigente' and rec.dias_sin_abono >= limite

    @api.constrains('factura_id', 'estado')
    def _check_una_cuenta_activa(self):
        for rec in self.filtered(lambda r: r.estado != 'anulada'):
            otras = self.search_count([
                ('factura_id', '=', rec.factura_id.id),
                ('estado', '!=', 'anulada'),
                ('id', '!=', rec.id),
            ])
            if otras:
                raise ValidationError(
                    "La factura %s ya tiene una cuenta de cobro activa." % rec.factura_id.name)

    # ------------------------------------------------------------------
    # Estados
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        cuentas = super().create(vals_list)
        cuentas._refrescar_estado()
        return cuentas

    def _refrescar_estado(self):
        """Recalcula Vigente / Vencida / Saldada y sincroniza el estado de la factura."""
        hoy = fields.Date.context_today(self)
        for rec in self.filtered(lambda r: r.estado != 'anulada'):
            if rec.currency_id.is_zero(rec.saldo_pendiente):
                nuevo = 'saldada'
            elif rec.fecha_vencimiento and rec.fecha_vencimiento < hoy:
                nuevo = 'vencida'
            else:
                nuevo = 'vigente'
            if nuevo != rec.estado:
                rec.write({'estado': nuevo})
            factura = rec.factura_id
            if nuevo == 'saldada' and factura.estado != 'pagada':
                factura.write({'estado': 'pagada'})
            elif nuevo != 'saldada' and factura.estado == 'pagada':
                factura.write({'estado': 'emitida'})

    @api.model
    def _cron_actualizar_vencidas(self):
        """Tarea diaria: actualiza estados, días sin abono y envía alertas."""
        abiertas = self.search([('estado', 'in', ESTADOS_ABIERTOS)])
        abiertas._refrescar_estado()
        abiertas._compute_alerta()
        abiertas._enviar_alertas()
        abiertas._enviar_avisos_vencimiento()

    # ------------------------------------------------------------------
    # Notificaciones
    # ------------------------------------------------------------------
    def _destinatarios_alerta(self):
        """Usuarios del grupo 'Alertas de cobro'; si no hay, quien creó la cuenta."""
        self.ensure_one()
        grupo = self.env.ref('caramia_facturacion.group_alertas_cobro', raise_if_not_found=False)
        usuarios = self.env['res.users']
        if grupo:
            campo = 'all_user_ids' if 'all_user_ids' in grupo._fields else 'users'
            usuarios = grupo[campo]
        if not usuarios:
            usuarios = self.create_uid or self.env.user
        return usuarios

    def _notificar(self, asunto, detalle):
        self.ensure_one()
        usuarios = self._destinatarios_alerta()
        if not usuarios:
            return
        saldo = formatLang(self.env, self.saldo_pendiente, currency_obj=self.currency_id)
        body = Markup(
            '<p>La factura <a href="#" data-oe-model="%s" data-oe-id="%s">%s</a> de <b>%s</b> '
            '%s. Saldo pendiente: <b>%s</b>.</p>'
        ) % (self._name, self.id, self.name, self.cliente_id.display_name, detalle, saldo)
        partners = usuarios.mapped('partner_id')

        # Mensaje en el chatter del documento: aparece en la bandeja de mensajes
        # del systray para los usuarios notificados (antes se usaba message_notify,
        # que solo genera un correo y no deja rastro visible dentro de Odoo).
        self.message_subscribe(partner_ids=partners.ids)
        self.message_post(
            body=body,
            subject=asunto,
            partner_ids=partners.ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        # Actividad: garantiza el aviso en el reloj de actividades del systray,
        # incluso si el usuario tiene desactivadas las notificaciones por correo.
        for usuario in usuarios:
            if self.activity_ids.filtered(
                    lambda a: a.user_id == usuario and a.summary == asunto):
                continue
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=asunto,
                note=body,
                user_id=usuario.id,
            )

    def _enviar_alertas(self):
        """Notifica las cuentas en alerta; repite cada N días mientras sigan sin abonos."""
        reenvio = int(self.env['ir.config_parameter'].sudo().get_param(
            'caramia_facturacion.dias_reenvio_alerta', 7))
        hoy = fields.Date.context_today(self)
        en_alerta = self.filtered('alerta_cobro')
        (self - en_alerta).filtered('fecha_ultima_alerta').write({'fecha_ultima_alerta': False})
        for rec in en_alerta:
            if rec.fecha_ultima_alerta and (hoy - rec.fecha_ultima_alerta).days < reenvio:
                continue
            rec._notificar(
                'Cuenta de cobro sin abonos: %s' % rec.name,
                Markup('lleva <b>%s días</b> sin abonos') % rec.dias_sin_abono)
            rec.fecha_ultima_alerta = hoy

    def _enviar_avisos_vencimiento(self):
        """Avisa una vez cuando está por vencer, y cada N días mientras esté vencida."""
        icp = self.env['ir.config_parameter'].sudo()
        dias_previos = int(icp.get_param('caramia_facturacion.dias_aviso_vencimiento', 3))
        reenvio = int(icp.get_param('caramia_facturacion.dias_reenvio_alerta', 7))
        hoy = fields.Date.context_today(self)
        for rec in self.filtered('fecha_vencimiento'):
            if rec.estado == 'vigente':
                faltan = (rec.fecha_vencimiento - hoy).days
                if 0 <= faltan <= dias_previos and not rec.fecha_aviso_por_vencer:
                    detalle = (Markup('vence en <b>%s</b> día(s)') % faltan) if faltan \
                        else Markup('vence <b>hoy</b>')
                    rec._notificar('Cuenta por vencer: %s' % rec.name, detalle)
                    rec.fecha_aviso_por_vencer = hoy
                elif faltan > dias_previos and rec.fecha_aviso_por_vencer:
                    rec.fecha_aviso_por_vencer = False
            elif rec.estado == 'vencida':
                if not rec.fecha_aviso_vencida or (hoy - rec.fecha_aviso_vencida).days >= reenvio:
                    dias = (hoy - rec.fecha_vencimiento).days
                    rec._notificar('Cuenta vencida: %s' % rec.name,
                                   Markup('está vencida hace <b>%s</b> día(s)') % dias)
                    rec.fecha_aviso_vencida = hoy

    # ------------------------------------------------------------------
    # Recordatorios por WhatsApp (Meta Cloud API)
    # ------------------------------------------------------------------
    @api.model
    def _wa_param(self, key, default=False):
        return self.env['ir.config_parameter'].sudo().get_param(
            'caramia_facturacion.wa_%s' % key, default)

    @api.model
    def _wa_activo(self):
        valor = str(self._wa_param('activo', '0')).strip().lower()
        return valor in ('1', 'true', 'yes', 'on')

    @api.model
    def _normalizar_telefono_wa(self, telefono):
        """Deja el número en formato internacional (Colombia por defecto)."""
        digitos = ''.join(filter(str.isdigit, telefono or ''))
        if not digitos:
            return ''
        if digitos.startswith('00'):
            digitos = digitos[2:]
        if len(digitos) == 10:
            digitos = '57' + digitos
        return digitos

    def _texto_recordatorio_wa(self):
        self.ensure_one()
        saldo = formatLang(self.env, self.saldo_pendiente, currency_obj=self.currency_id)
        fecha = self.fecha_vencimiento.strftime('%d/%m/%Y') if self.fecha_vencimiento else ''
        return (
            'Estimado/a *%s*,\n\n'
            'Le recordamos desde *Calzado Cara Mía* que tiene una deuda pendiente de '
            '*%s* correspondiente a la factura *%s*, con fecha de corte *%s*.\n\n'
            'Por favor comuníquese con nosotros para gestionar su pago. ¡Gracias!'
        ) % (self.cliente_id.nombre_cliente, saldo, self.name, fecha)

    def _payload_recordatorio_wa(self):
        self.ensure_one()
        telefono = self._normalizar_telefono_wa(self.cliente_id.telefono_cliente)
        plantilla = (self._wa_param('template') or '').strip()
        payload = {
            'messaging_product': 'whatsapp',
            'to': telefono,
        }
        if plantilla:
            saldo = formatLang(self.env, self.saldo_pendiente, currency_obj=self.currency_id)
            fecha = self.fecha_vencimiento.strftime('%d/%m/%Y') if self.fecha_vencimiento else ''
            payload.update({
                'type': 'template',
                'template': {
                    'name': plantilla,
                    'language': {'code': self._wa_param('template_lang', 'es') or 'es'},
                    'components': [{
                        'type': 'body',
                        'parameters': [
                            {'type': 'text', 'text': self.cliente_id.nombre_cliente or ''},
                            {'type': 'text', 'text': str(saldo)},
                            {'type': 'text', 'text': self.name or ''},
                            {'type': 'text', 'text': fecha},
                        ],
                    }],
                },
            })
        else:
            payload.update({
                'type': 'text',
                'text': {'body': self._texto_recordatorio_wa(), 'preview_url': False},
            })
        return telefono, payload

    def _enviar_recordatorio_whatsapp(self):
        """Envía un recordatorio al teléfono registrado del cliente. Devuelve True/False."""
        self.ensure_one()
        telefono = self._normalizar_telefono_wa(self.cliente_id.telefono_cliente)
        if not telefono:
            self.write({'recordatorio_wa_estado': 'Sin teléfono registrado'})
            return False

        token = self._wa_param('token') or os.getenv('WHATSAPP_API_TOKEN', '')
        phone_id = self._wa_param('phone_id') or os.getenv('WHATSAPP_PHONE_ID', '')
        version = self._wa_param('api_version', 'v22.0') or 'v22.0'
        if not token or not phone_id:
            self.write({'recordatorio_wa_estado': 'Falta token o phone_number_id'})
            return False

        _telefono, payload = self._payload_recordatorio_wa()
        url = 'https://graph.facebook.com/%s/%s/messages' % (version, phone_id)
        headers = {
            'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json',
        }
        try:
            respuesta = requests.post(url, json=payload, headers=headers, timeout=20)
            datos = respuesta.json() if respuesta.content else {}
            if respuesta.status_code in (200, 201):
                self.write({
                    'fecha_recordatorio_wa': fields.Date.context_today(self),
                    'recordatorio_wa_estado': 'Enviado',
                })
                self.message_post(
                    body=Markup('<p>Recordatorio de WhatsApp enviado a <b>%s</b> (%s).</p>')
                    % (self.cliente_id.display_name, telefono),
                    subtype_xmlid='mail.mt_note',
                )
                return True
            error = (datos.get('error') or {}).get('message') or respuesta.text[:250]
            self.write({'recordatorio_wa_estado': 'Error: %s' % error})
            _logger.warning('WhatsApp recordatorio %s: %s', self.name, respuesta.text)
        except Exception as error:
            self.write({'recordatorio_wa_estado': 'Error: %s' % str(error)[:250]})
            _logger.exception('WhatsApp recordatorio %s', self.name)
        return False

    @api.model
    def _cron_recordatorios_whatsapp(self):
        """Recordatorio diario a las cuentas con más de N días desde la fecha de corte."""
        if not self._wa_activo():
            return
        dias_gracia = int(self._wa_param('dias_gracia', 3) or 3)
        dias_reenvio = int(self._wa_param('dias_reenvio', 7) or 7)
        hoy = fields.Date.context_today(self)
        limite = hoy - timedelta(days=dias_gracia)
        cuentas = self.search([
            ('estado', 'in', ESTADOS_ABIERTOS),
            ('saldo_pendiente', '>', 0),
            ('fecha_vencimiento', '<=', limite),
        ])
        for rec in cuentas:
            if not (rec.cliente_id.telefono_cliente or '').strip():
                continue
            if (rec.fecha_recordatorio_wa
                    and (hoy - rec.fecha_recordatorio_wa).days < dias_reenvio):
                continue
            rec._enviar_recordatorio_whatsapp()

    def action_enviar_recordatorio_whatsapp(self):
        enviados = sum(1 for rec in self if rec._enviar_recordatorio_whatsapp())
        if enviados:
            titulo, tipo = 'WhatsApp', 'success'
            mensaje = 'Recordatorio enviado a %s cliente(s).' % enviados
        else:
            titulo, tipo = 'WhatsApp', 'warning'
            mensaje = 'No se pudo enviar. Revise el teléfono del cliente y la configuración.'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': titulo,
                'message': mensaje,
                'type': tipo,
                'sticky': False,
            },
        }

    # ------------------------------------------------------------------
    # Resumen para las tarjetas de la lista de clientes
    # ------------------------------------------------------------------
    @api.model
    def get_resumen_cartera(self):
        datos = self._read_group(
            [('estado', 'in', ESTADOS_ABIERTOS)], [],
            ['monto_total:sum', 'total_abonado:sum', 'saldo_pendiente:sum'])
        facturado, abonado, saldo = datos[0] if datos else (0.0, 0.0, 0.0)
        moneda = self.env.company.currency_id
        return {
            'facturado': facturado or 0.0,
            'abonado': abonado or 0.0,
            'saldo': saldo or 0.0,
            'moneda': moneda.name,
            'decimales': moneda.decimal_places,
        }

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def action_anular(self):
        self.ensure_one()
        if self.estado not in ESTADOS_ABIERTOS:
            raise UserError("Solo se pueden anular cuentas vigentes o vencidas.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Anular cuenta de cobro',
            'res_model': 'cara.mia.cuenta.anular.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cuenta_id': self.id},
        }

    def action_registrar_pago(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar pago',
            'res_model': 'cara.mia.pago.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_cliente_id': self.cliente_id.id,
                'default_cuenta_id': self.id,
                'solo_cuenta_id': self.id,
            },
        }

    def action_ver_factura(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura',
            'res_model': 'cara.mia.facturacion',
            'res_id': self.factura_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        }


class CaramiaCliente(models.Model):
    """Extiende el cliente con su cartera. SIN _name: es la misma tabla de clientes."""
    _inherit = 'cara.mia.cliente'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    cuenta_cobro_ids = fields.One2many('cara.mia.cuenta.cobro', 'cliente_id',
                                       string='Todas las Cuentas de Cobro')
    cuenta_activa_ids = fields.One2many(
        'cara.mia.cuenta.cobro', 'cliente_id', string='Facturas Activas',
        domain=[('estado', 'in', ESTADOS_ABIERTOS)])

    facturacion_ids = fields.One2many('cara.mia.facturacion', 'cliente_id', string='Todas las Facturas')
    factura_activa_ids = fields.One2many(
        'cara.mia.facturacion', 'cliente_id', string='Facturas Activas',
        domain=[('estado', 'in', ('borrador', 'emitida'))])

    total_facturado_cuentas = fields.Monetary(string='Total Facturado', compute='_compute_cartera_cliente')
    total_abonado_cuentas = fields.Monetary(string='Total Abonado', compute='_compute_cartera_cliente')
    saldo_pendiente_cuentas = fields.Monetary(string='Saldo Total Adeudado',
                                              compute='_compute_cartera_cliente')

    @api.depends('cuenta_cobro_ids.estado', 'cuenta_cobro_ids.monto_total',
                 'cuenta_cobro_ids.total_abonado', 'cuenta_cobro_ids.saldo_pendiente')
    def _compute_cartera_cliente(self):
        for rec in self:
            activas = rec.cuenta_cobro_ids.filtered(lambda c: c.estado in ESTADOS_ABIERTOS)
            rec.total_facturado_cuentas = sum(activas.mapped('monto_total'))
            rec.total_abonado_cuentas = sum(activas.mapped('total_abonado'))
            rec.saldo_pendiente_cuentas = sum(activas.mapped('saldo_pendiente'))
            
    def action_registrar_abono(self):
        """Abre el wizard de pago con el cliente ya seleccionado."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar abono',
            'res_model': 'cara.mia.pago.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cliente_id': self.id},
        }


class CaramiaCuentaCobroPago(models.Model):
    _name = 'cara.mia.cuenta.cobro.pago'
    _description = 'Pago / Abono de Cuenta de Cobro'
    _order = 'fecha desc, id desc'

    cuenta_id = fields.Many2one('cara.mia.cuenta.cobro', string='Cuenta de Cobro',
                                required=True, ondelete='cascade', index=True)
    factura_id = fields.Many2one(related='cuenta_id.factura_id', string='Factura', store=True)
    cliente_id = fields.Many2one(related='cuenta_id.cliente_id', string='Cliente', store=True)
    currency_id = fields.Many2one(related='cuenta_id.currency_id')

    fecha = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    monto = fields.Monetary(string='Monto', required=True)
    tipo = fields.Selection([('abono', 'Abono'), ('pago', 'Pago total')],
                            string='Tipo', readonly=True)
    metodo = fields.Selection(METODOS_PAGO, string='Forma de Pago', default='efectivo', required=True)
    referencia = fields.Char(string='N° Comprobante')
    observacion = fields.Char(string='Observación')

    @api.constrains('monto')
    def _check_monto_positivo(self):
        for rec in self:
            if rec.monto <= 0:
                raise ValidationError("El monto del pago debe ser mayor a cero.")

    @api.constrains('monto', 'cuenta_id')
    def _check_no_excede_el_total(self):
        for cuenta in self.mapped('cuenta_id'):
            pagado = sum(cuenta.pago_ids.mapped('monto'))
            if cuenta.currency_id.compare_amounts(pagado, cuenta.monto_total) > 0:
                raise ValidationError(
                    "Los pagos de la factura %s (%s) superan su valor total (%s)."
                    % (cuenta.name, pagado, cuenta.monto_total))

    def _check_editable(self):
        if any(p.cuenta_id.estado == 'anulada' for p in self):
            raise UserError("No se pueden modificar los pagos de una cuenta anulada.")

    @api.model_create_multi
    def create(self, vals_list):
        Cuenta = self.env['cara.mia.cuenta.cobro']
        for vals in vals_list:
            cuenta = Cuenta.browse(vals.get('cuenta_id'))
            if cuenta.estado in ('saldada', 'anulada'):
                raise UserError(
                    "La cuenta de la factura %s está %s y no admite más pagos."
                    % (cuenta.name, cuenta.estado))
            alcanza = cuenta.currency_id.compare_amounts(
                vals.get('monto', 0.0), cuenta.saldo_pendiente) >= 0
            vals['tipo'] = 'pago' if alcanza else 'abono'
        pagos = super().create(vals_list)
        pagos.mapped('cuenta_id')._refrescar_estado()
        return pagos

    def write(self, vals):
        self._check_editable()
        res = super().write(vals)
        self.mapped('cuenta_id')._refrescar_estado()
        return res

    def unlink(self):
        self._check_editable()
        cuentas = self.mapped('cuenta_id')
        res = super().unlink()
        cuentas._refrescar_estado()
        return res