{
    'name': 'Cara Mia - Costos',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing/Sales',
    'summary': 'Gestión de cotizaciones, hojas de costo por par o docena y conversión a órdenes de producción',
    'description': """ hola
    """,
    'author': 'Adriana Milena Amaya Llerena',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'caramia_production',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/costos_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}