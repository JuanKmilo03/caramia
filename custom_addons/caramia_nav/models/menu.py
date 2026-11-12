from odoo import models, fields


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    x_caramia_descripcion = fields.Text(
        string="Descripción corta",
        help="Descripción corta del encabezado. En el menú raíz (app) es la "
        "descripción de la app; en una sección (hijo directo) la sobreescribe.",
    )
    x_caramia_boton_etiqueta = fields.Char(
        string="Etiqueta del botón principal",
        help="Texto del botón dorado del encabezado (ej. 'Exportar cartera', "
        "'Nueva orden'). Si se define en la sección activa, cambia por pestaña; "
        "si no, se usa el del menú raíz (app).",
    )
    x_caramia_boton_accion = fields.Char(
        string="Acción o URL del botón",
        help="Identificador XML de una acción (ej. caramia_customer.action_cliente) "
        "o una URL absoluta (https://...). Vacío = sin botón. Mismo criterio de "
        "precedencia: sección activa > menú raíz.",
    )
