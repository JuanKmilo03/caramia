from odoo import models, fields

class CaramiaEmployee(models.Model):
    _name = 'cara.mia.empleado'
    _description = 'Empleado Caramia'
    _rec_name = 'nombre_empleado'

    empleado_id = fields.Char(
        string='Cédula', 
        required=True, 
        copy=False,
        index=True
    )
    nombre_empleado = fields.Char(string='Nombre Completo', required=True)
    telefono_empleado = fields.Char(string='Teléfono', required=True)

    tipo_labor_id = fields.Many2one(
        'cara.mia.tipo.labor', 
        string='Labor', 
        required=True,
        ondelete='restrict'
    )
    
    registro_trabajo_orden_ids = fields.One2many(
            'cara.mia.registro.trabajo.orden', 
            'empleado_id', 
            string='Historial de Trabajos'
        )

    _sql_constraints = [
        ('empleado_id_unique', 'unique(empleado_id)', 'La cédula/documento ingresado ya está registrado para otro empleado.')
    ]