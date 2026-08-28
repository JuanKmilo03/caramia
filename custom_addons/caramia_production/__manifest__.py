{
    'name': 'Cara Mia - Órdenes de Producción',
    'version': '1.0',
    'category': 'Manufacturing',
    'depends': ['mrp', 'caramia_catalog', 'caramia_invoicing'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
}
