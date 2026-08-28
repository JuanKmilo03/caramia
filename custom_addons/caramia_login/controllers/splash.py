import logging
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

SAFE_PREFIXES = ("/odoo", "/web")

def _safe_redirect(redirect=None, kw=None):
    """Busca el redirect en todos los lugares posibles y valida que sea seguro."""
    url = redirect or (kw or {}).get("redirect") or "/odoo"
    if any(url.startswith(p) for p in ("/odoo", "/web")):
        return url
    return "/odoo"

def _add_splash(url):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}splash=1"


class CaramiaHome(Home):

    def web_login(self, redirect=None, **kw):
        response = super().web_login(redirect=redirect, **kw)
        if request.httprequest.method == "POST" and request.session.uid:
            return request.redirect(_add_splash("/odoo"))
        return response


class CaramiaAuthSignupHome(AuthSignupHome):

    def web_auth_signup(self, *args, **kw):
        response = super().web_auth_signup(*args, **kw)
        if request.session.uid:
            dest = request.params.get("redirect") or kw.get("redirect") or "/odoo"
            if not any(dest.startswith(p) for p in ("/odoo", "/web")):
                dest = "/odoo"
            return request.redirect(_add_splash(dest))
        return response

    def web_auth_reset_password(self, *args, **kw):
        response = super().web_auth_reset_password(*args, **kw)
        
        uid = request.session.uid
        if not uid and request.httprequest.method == "POST":
            login = kw.get('login') or request.params.get('login')
            password = kw.get('password') or request.params.get('password')
            if login and password:
                uid = request.session.authenticate(request.session.db, login, password)

        if uid:
            dest = request.params.get("redirect") or kw.get("redirect") or "/odoo"
            if not any(dest.startswith(p) for p in ("/odoo", "/web")):
                dest = "/odoo"
            return request.redirect(_add_splash(dest))
            
        return response

try:
    from odoo.addons.auth_oauth.controllers.main import OAuthLogin

    class CaramiaOAuthLogin(OAuthLogin):

        def signin(self, **kw):
            response = super().signin(**kw)
            if request.session.uid:
                return request.redirect(_add_splash(_safe_redirect(kw.get("redirect"))))
            return response

except ImportError:
    _logger.debug("caramia_login: auth_oauth no disponible.")