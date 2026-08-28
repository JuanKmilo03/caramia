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
}
