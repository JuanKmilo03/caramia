{
    "name": "Cara Mia - Navegación y Encabezado de Apps",
    "version": "18.0.1.0.0",
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
        # views/menu_views.xml NO se auto-carga: el inherit_id de la vista de formulario
        # de ir.ui.menu depende de cada build de Odoo 18 (en esta instalación
        # "web.menu_form_view" no existe). Los campos x_caramia_* se definen en
        # models/menu.py y Odoo los expone en vistas automáticas.
        # Cuando confirmes el external ID correcto de la vista de formulario de
        # ir.ui.menu, descomenta la línea siguiente y actualiza el módulo.
        # "views/menu_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "caramia_nav/static/src/scss/caramia_nav.scss",
            "caramia_nav/static/src/js/navbar_patch.esm.js",
            "caramia_nav/static/src/js/header_tabs.esm.js",
            "caramia_nav/static/src/xml/caramia_nav.xml",
        ],
    },
}
