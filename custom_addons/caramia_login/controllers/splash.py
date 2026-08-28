import logging
import hashlib
from datetime import date
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

_GREETING_TEMPLATES = [
    "Empecemos a trabajar,",
    "Hola de nuevo,",
    "Hola, {name} ¿Qué haremos hoy?",  # esta plantilla lleva el nombre dentro
]

def _pick_greeting(name: str) -> str:
    """
    Rota entre las frases usando el día + nombre como semilla,
    así cambia cada día pero es consistente durante la misma sesión.
    """
    seed = f"{date.today().isoformat()}-{name}"
    index = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(_GREETING_TEMPLATES)
    template = _GREETING_TEMPLATES[index]

    # Si la plantilla ya incluye {name} (tercera frase), no lo agregamos aparte
    if "{name}" in template:
        return template.replace("{name}", name)
    return template  # el nombre lo agrega el JS aparte


def _add_splash_param(url: str, greeting: str = "") -> str:
    """Añade ?splash=1&greeting=... a la URL de destino."""
    if not url:
        url = "/odoo"
    sep = "&" if "?" in url else "?"
    from urllib.parse import quote
    return f"{url}{sep}splash=1&greeting={quote(greeting)}"


class CaramiaHome(Home):

    def web_login(self, redirect=None, **kw):
        response = super().web_login(redirect=redirect, **kw)
        if request.httprequest.method == "POST" and request.session.uid:
            name = (request.env.user.name or "Usuario").split()[0]
            greeting = _pick_greeting(name)
            dest = _add_splash_param(redirect or "/odoo", greeting)
            return request.redirect(dest)
        return response


class CaramiaAuthSignupHome(AuthSignupHome):

    def web_auth_signup(self, *args, **kw):
        response = super().web_auth_signup(*args, **kw)
        if request.session.uid:
            name = (request.env.user.name or "Usuario").split()[0]
            greeting = _pick_greeting(name)
            return request.redirect(_add_splash_param(kw.get("redirect") or "/odoo", greeting))
        return response

    def web_auth_reset_password(self, *args, **kw):
        response = super().web_auth_reset_password(*args, **kw)
        if request.session.uid:
            name = (request.env.user.name or "Usuario").split()[0]
            greeting = _pick_greeting(name)
            return request.redirect(_add_splash_param(kw.get("redirect") or "/odoo", greeting))
        return response


try:
    from odoo.addons.auth_oauth.controllers.main import OAuthLogin

    class CaramiaOAuthLogin(OAuthLogin):

        def signin(self, **kw):
            response = super().signin(**kw)
            if request.session.uid:
                name = (request.env.user.name or "Usuario").split()[0]
                greeting = _pick_greeting(name)
                dest = _add_splash_param(kw.get("redirect") or "/odoo", greeting)
                return request.redirect(dest)
            return response

except ImportError:
    _logger.debug("caramia_login: auth_oauth no disponible.")