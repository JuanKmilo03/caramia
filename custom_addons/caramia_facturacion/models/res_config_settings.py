from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Alertas internas de cartera
    caramia_dias_alerta_sin_abono = fields.Integer(
        string='Días sin abono para alertar',
        config_parameter='caramia_facturacion.dias_alerta_sin_abono',
        default=7,
        help='Una cuenta vigente entra en alerta cuando lleva estos días sin abonos.',
    )
    caramia_dias_reenvio_alerta = fields.Integer(
        string='Días entre reenvíos de alerta',
        config_parameter='caramia_facturacion.dias_reenvio_alerta',
        default=4,
    )
    caramia_dias_aviso_vencimiento = fields.Integer(
        string='Días antes del vencimiento para avisar',
        config_parameter='caramia_facturacion.dias_aviso_vencimiento',
        default=2,
    )

    # Recordatorios por WhatsApp (Meta Cloud API)
    caramia_wa_activo = fields.Boolean(
        string='Activar recordatorios WhatsApp',
        config_parameter='caramia_facturacion.wa_activo',
    )
    caramia_wa_dias_gracia = fields.Integer(
        string='Días después de la fecha de corte',
        config_parameter='caramia_facturacion.wa_dias_gracia',
        default=3,
        help='Solo se recuerdan las cuentas con saldo cuya fecha de corte '
             '(vencimiento) superó estos días.',
    )
    caramia_wa_dias_reenvio = fields.Integer(
        string='Días entre recordatorios',
        config_parameter='caramia_facturacion.wa_dias_reenvio',
        default=7,
    )
    caramia_wa_phone_id = fields.Char(
        string='Phone Number ID de Meta',
        config_parameter='caramia_facturacion.wa_phone_id',
    )
    caramia_wa_token = fields.Char(
        string='Token de acceso Meta',
        config_parameter='caramia_facturacion.wa_token',
    )
    caramia_wa_api_version = fields.Char(
        string='Versión Graph API',
        config_parameter='caramia_facturacion.wa_api_version',
        default='v22.0',
    )
    caramia_wa_template = fields.Char(
        string='Plantilla de mensaje',
        config_parameter='caramia_facturacion.wa_template',
        help='Nombre de la plantilla aprobada en Meta. Si se deja vacío se envía '
             'texto libre (solo válido dentro de la ventana de 24 horas).',
    )
    caramia_wa_template_lang = fields.Char(
        string='Idioma de la plantilla',
        config_parameter='caramia_facturacion.wa_template_lang',
        default='es',
    )
