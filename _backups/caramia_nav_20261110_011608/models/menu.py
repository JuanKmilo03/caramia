from odoo import models, fields


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    x_caramia_descripcion = fields.Text(
        string="Descripción corta",
        help="Descripción corta que se muestra en el encabezado de la app, debajo del título. "
        "Solo aplica a los menús raíz (apps). Configurable sin tocar JS.",
    )
    x_caramia_boton_etiqueta = fields.Char(
        string="Etiqueta del botón principal",
        help="Texto del botón de acción principal del encabezado (ej. 'Exportar cartera', 'Nueva orden'). "
        "Queda igual para toda la app, no varía por pestaña.",
    )
    x_caramia_boton_accion = fields.Char(
        string="Acción o URL del botón",
        help="Identificador XML de una acción (ej. caramia_customer.action_cliente) o una URL absoluta "
        "(https://...). Déjalo vacío si no quieres mostrar el botón principal en esta app.",
    )
