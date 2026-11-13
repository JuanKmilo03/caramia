{
    "name": "Cara Mia - Navegación y Encabezado de Apps",
    "version": "18.0.1.0.11",
    "category": "Web",
    "summary": "Navbar, encabezado de página y pestañas de sección personalizados para las apps de Caramia",
    "author": "Tu Equipo",
    "website": "",
    "license": "LGPL-3",
    "depends": ["web"],
    "application": False,
    "installable": True,
    "auto_install": False,
    "data": [
        "views/menu_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "caramia_nav/static/src/scss/caramia_nav.scss",
            "caramia_nav/static/src/js/utils.esm.js",
            "caramia_nav/static/src/js/app_switcher.esm.js",
            "caramia_nav/static/src/js/header_tabs.esm.js",
            "caramia_nav/static/src/xml/caramia_nav.xml",
        ],
    },
}
