{
    'name': 'Cara Mia Login',
    'version': '18.0.1.0.0',
    'category': 'Hidden',
    'summary': 'Personalización del inicio de sesión',
    'depends': [
        'web',
        'auth_oauth',
    ],
    'assets': {
        'web.assets_frontend': [
        'caramia_login/static/src/scss/caramia_login.scss',
        'caramia_login/static/src/js/shader_fondo.js',

    ],
        'web.assets_backend': [
            'caramia_login/static/src/scss/splash.scss',
            'caramia_login/static/src/js/splash_owl.js',
        ],
    },
    'installable': True,
    'application': False,
}