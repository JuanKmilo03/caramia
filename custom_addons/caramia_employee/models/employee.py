from odoo import models, fields, api

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
    job_title = fields.Char(string='Cargo', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('employee_code', 'Nuevo') == 'Nuevo':
                vals['employee_code'] = self.env['ir.sequence'].next_by_code('caramia.employee.sequence') or 'Nuevo'
        return super().create(vals_list)