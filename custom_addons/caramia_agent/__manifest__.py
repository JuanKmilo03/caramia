{
    'name': 'Cara Mia - Agente IA',
    'version': '1.0',
    'category': 'Productivity',
    'summary': 'Asistente de Inteligencia Artificial para Cara Mia',
    'depends': ['base', 'web'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'caramia_agent/static/src/css/chat_flotante.css',
            'caramia_agent/static/src/js/chat_flotante.js',
        ],
    },
    'installable': True,
    'application': True,
}