{
    'name': 'Cara Mia - Personal y Destajo',
    'version': '1.1',
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
}
