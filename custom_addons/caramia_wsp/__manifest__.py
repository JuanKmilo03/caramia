{
    'name': 'Cara Mía - WhatsApp y Recordatorios de Cartera',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Módulo para configurar API de WhatsApp y enviar recordatorios masivos por lotes',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_config_views.xml',
        'views/whatsapp_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}