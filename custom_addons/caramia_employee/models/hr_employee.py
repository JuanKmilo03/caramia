from odoo import models, fields


class CaramiaEmployeeRole(models.Model):
    _name = 'caramia.employee.role'
    _description = 'Rol de fábrica'
    _order = 'name'

    name = fields.Char(string='Rol', required=True)
    code = fields.Char(string='Código')
    price_per_pair = fields.Monetary(
        string='Precio por par', required=True, default=0.0,
        currency_field='currency_id',
        help='Tarifa base que se aplica a cada par fabricado por este rol.',
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Observaciones')

    _sql_constraints = [
        ('caramia_employee_role_name_uniq', 'unique(name)', 'El nombre del rol debe ser único.'),
    ]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # =========================================================
    # IDENTIFICACIÓN PERSONAL
    # =========================================================

    document_type = fields.Selection(
        [
            ('cc', 'Cédula de Ciudadanía'),
            ('ce', 'Cédula de Extranjería'),
            ('passport', 'Pasaporte'),
            ('other', 'Otro'),
        ],
        string='Tipo de Documento',
        default='cc',
    )

    document_number = fields.Char(
        string='Número de Documento'
    )

    # =========================================================
    # CONTACTO PERSONAL
    # =========================================================

    personal_phone = fields.Char(
        string='Teléfono Personal'
    )

    personal_address = fields.Char(
        string='Dirección de Residencia'
    )

    # =========================================================
    # CONTACTO DE EMERGENCIA
    # =========================================================

    emergency_contact_name = fields.Char(
        string='Nombre Contacto de Emergencia'
    )

    emergency_contact_phone = fields.Char(
        string='Teléfono Contacto de Emergencia'
    )

    # =========================================================
    # OBSERVACIONES
    # =========================================================

    personal_notes = fields.Text(
        string='Observaciones'
    )

    # =========================================================
    # INFORMACIÓN DE FÁBRICA
    # =========================================================

    factory_role_id = fields.Many2one(
        'caramia.employee.role',
        string='Rol en fábrica',
        domain="[('active', '=', True)]",
    )
    factory_entry_date = fields.Date(string='Fecha de ingreso a fábrica')
