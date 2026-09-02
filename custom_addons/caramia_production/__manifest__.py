{
    'name': 'Caramia Producción',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Módulo de producción de calzado con curva de tallas e historial',
    'depends': ['base', 'product', 'web', 'mail', 'caramia_customer'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/production_views.xml',
        'reports/report_caramia_production.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}