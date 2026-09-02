{
    'name': 'Caramia Clientes',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Gestión aislada e independiente de clientes con ID incremental y sello',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/customer_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}