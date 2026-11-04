{
    'name': 'Cara Mia - Agente IA',
    'version': '1.0',
    'category': 'Productivity',
    'summary': 'Asistente de Inteligencia Artificial para Cara Mia',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'caramia_agent/static/src/css/chat_flotante.css',
            'caramia_agent/static/src/js/chat_flotante.js',
            'caramia_agent/static/src/js/voice_chat.js',
        ],
    },
    'installable': True,
    'application': True,
}