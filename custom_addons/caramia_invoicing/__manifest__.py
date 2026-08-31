{
    'name': 'Cara Mia - Facturación y Clientes',
    'version': '1.1.0',
    'category': 'Sales',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'caramia_invoicing/static/src/css/client_style.css',
        ],
    },
    'installable': True,
    'application': True,
    'name': 'Cara Mia - Facturación y Cartera',
    'version': '1.0',
    'category': 'Accounting',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
