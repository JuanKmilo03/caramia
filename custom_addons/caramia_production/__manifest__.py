{
    'name': 'Caramia Producción',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Módulo de producción de calzado con curva de tallas e historial',
    'depends': [
        'base', 'product', 'web', 'mail',  'web_editor',
        'caramia_customer', 'caramia_references', 'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/production_views.xml',
        'wizard/lista_compras_wizard_views.xml',
        'views/production_compra_views.xml',
        'reports/production_reports.xml',
        'reports/production_templates.xml',
        'reports/lista_compras_production_report.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}