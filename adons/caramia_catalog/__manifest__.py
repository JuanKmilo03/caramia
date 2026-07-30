{
    'name': 'Cara Mia - Catálogo y Referencias',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Fichas técnicas y catálogo de modelos de calzado',
    'depends': ['product', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/shoe_reference_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'caramia_catalog/static/src/css/catalog_style.css',
        ],
    },
    'installable': True,
    'application': False,
}
