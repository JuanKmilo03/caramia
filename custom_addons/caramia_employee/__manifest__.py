{
    'name': 'Caramia Empleados',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Gestión simplificada e independiente de empleados',
    'depends': ['base', 'caramia_references', 'caramia_production'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_views.xml',
        'views/registro_trabajo_orden_views.xml',
        'views/pago_empleado_views.xml',
        'views/liquidacion_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}