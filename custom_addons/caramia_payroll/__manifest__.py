{
    'name': 'Cara Mia - Personal y Destajo',
<<<<<<< HEAD
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
=======
    'version': '1.0',
    'category': 'Human Resources',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
>>>>>>> 7b3cf60954591c2500e070eba99a787916a186fc
}
