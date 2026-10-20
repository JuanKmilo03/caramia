{
    'name': 'Cara Mia - Facturación y Cobros',
    'version': '1.0',
    'summary': 'Gestión de Facturas, Cuentas de Cobro y Abonos',
    'description': 'Módulo para automatizar facturación desde Órdenes de Producción finalizadas y gestionar cuentas por cobrar.',
    'category': 'Accounting',
    'depends': ['base', 'mail', 'caramia_production', 'caramia_customer'],
    'data': [
        'security/cobros_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_fac.xml',
        'data/sequence_cc.xml',
        'data/cuenta_cobro_cron.xml',
        'wizard/cuenta_cobro_wizard_views.xml',
        'views/cxc_views.xml',
        'views/facturacion_views.xml',
        'reports/facturacion_report.xml',
    ],
    
    'installable': True,
    'application': True,
}