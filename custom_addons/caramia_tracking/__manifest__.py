{
    'name': 'Caramia Seguimiento de Producción',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Avance por labor, alertas de estancamiento y estadísticas de producción',
    'depends': ['mail', 'caramia_production', 'caramia_employee'],
    'data': [
        'security/production_security.xml',
        'data/production_cron.xml',
        'views/production_tracking_views.xml',
        'views/production_tracking_dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'caramia_tracking/static/src/js/tracking_dashboard.js',
            'caramia_tracking/static/src/xml/tracking_dashboard.xml',
            'caramia_tracking/static/src/scss/tracking_dashboard.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
