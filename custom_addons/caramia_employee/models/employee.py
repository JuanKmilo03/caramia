from odoo import models, fields

class CaramiaEmployeeJob(models.Model):
    _name = 'caramia.employee.job'
    _description = 'Cargo / Puesto de Trabajo'
    _order = 'name'

    name = fields.Char(string='Nombre del Cargo', required=True)


class CaramiaEmployee(models.Model):
    _name = 'caramia.employee'
    _description = 'Empleado Caramia'
    _order = 'name, id desc'

    employee_code = fields.Char(
        string='Cédula / Documento', 
        required=True, 
        copy=False,
        index=True
    )
    name = fields.Char(string='Nombre Completo', required=True)
    job_id = fields.Many2one(
        'caramia.employee.job', 
        string='Cargo / Puesto', 
        required=True,
        ondelete='restrict'
    )
    phone = fields.Char(string='Teléfono', required=True)

    _sql_constraints = [
        ('employee_code_unique', 'unique(employee_code)', 'La cédula/documento ingresado ya está registrado para otro empleado.')
    ]