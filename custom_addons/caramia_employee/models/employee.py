from odoo import models, fields, api

class CaramiaEmployeeJob(models.Model):
    _name = 'caramia.employee.job'
    _description = 'Cargo / Puesto de Trabajo'
    _order = 'name'

    name = fields.Char(string='Nombre del Cargo', required=True)

class CaramiaEmployee(models.Model):
    _name = 'caramia.employee'
    _description = 'Empleado Caramia'
    _order = 'employee_code desc, id desc'

    employee_code = fields.Char(
        string='ID Empleado', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='Nuevo'
    )
    name = fields.Char(string='Nombre Completo', required=True)
    job_id = fields.Many2one(
        'caramia.employee.job', 
        string='Cargo / Puesto', 
        required=True,
        ondelete='restrict'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('employee_code', 'Nuevo') == 'Nuevo':
                vals['employee_code'] = self.env['ir.sequence'].next_by_code('caramia.employee.sequence') or 'Nuevo'
        return super().create(vals_list)