{
    'name': 'Cara Mia - Gestión de Referencias',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Módulo para el control de referencias, fichas técnicas e insumos de calzado',
    'author': 'Adriana Amaya Llerena',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/referencia_views.xml',
        'data/secuencia_ref.xml',
    ],
    'installable': True,
    'application': True,
}