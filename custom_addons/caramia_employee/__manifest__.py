{
    'name': 'Caramia Empleados',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Gestión simplificada e independiente de empleados',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}