{
    'name': 'Cara Mia - Gestión de Empleados',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Personalización de la gestión de empleados de Cara Mia',

    'depends': [
        'hr',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/employee_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'caramia_employee/static/src/employe_style.css',
        ],
    },

    'installable': True,
    'application': True,
}