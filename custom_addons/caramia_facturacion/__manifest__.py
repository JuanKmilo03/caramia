{
    'name': 'Cara Mia - Facturación y Cobros',
    'version': '1.0',
    'summary': 'Gestión de Facturas, Cuentas de Cobro y Abonos',
    'description': 'Módulo para automatizar facturación desde Órdenes de Producción finalizadas y gestionar cuentas por cobrar.',
    'category': 'Accounting',
    'depends': ['base', 'mail', 'caramia_production', 'caramia_customer'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/facturacion_views.xml',
        'reports/facturacion_report.xml',
    ],
    'installable': True,
    'application': True,
}