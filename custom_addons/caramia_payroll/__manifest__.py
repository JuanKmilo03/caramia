{
    'name': 'Cara Mia - Personal y Destajo',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/payroll_views.xml',
    ],
    'installable': True,
    'application': True,
    #'assets': {
    #    'web.assets_backend': [
    #        'caramia_payroll/static/src/css/payroll_style.css',
    #    ],
    #},
    'depends': ['base', 'hr', 'caramia_employee', 'caramia_production'],
    'version': '1.0',
    'category': 'Human Resources',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
}
