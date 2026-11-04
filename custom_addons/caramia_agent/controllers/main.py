import os
import hmac
import hashlib
import requests
from odoo import http
from odoo.http import request

# Importamos nuestro Despachador Genérico
from ..ai_actions.dispatcher import procesar_accion_ia

class AgenteController(http.Controller):
    
    def _recuperar_contexto(self, mensaje):
        contexto = ""
        try:
            palabras = [p for p in (mensaje or "").split() if len(p) > 3][:5]
            dominio = []
            for p in palabras:
                dominio.append(('content', 'ilike', p))
            # OR entre palabras: usar '|' (Odoo domain OR)
            if len(dominio) > 1:
                or_domain = ['|'] * (len(dominio) - 1) + dominio
            else:
                or_domain = dominio
            docs = self.env['caramia.agent.knowledge'].search(or_domain, limit=5) if dominio else self.env['caramia.agent.knowledge'].search([], limit=5)
            if docs:
                contexto += "CONOCIMIENTO RELEVANTE:\n"
                for d in docs:
                    contexto += f"- {d.name}: {d.content}\n"
            corrs = self.env['caramia.agent.correction'].search([], order='create_date desc', limit=5)
            if corrs:
                contexto += "\nCORRECCIONES PREVIAS:\n"
                for c in corrs:
                    contexto += f"- Pregunta: {c.pregunta}\n  Correccion: {c.correccion}\n"
        except Exception:
            pass
        return contexto

    @http.route('/caramia/chat', type='json', auth='user')
    def enviar_mensaje_ia(self, mensaje):
        url_fastapi = os.getenv("FASTAPI_URL", "http://fastapi_ai:8000") + "/api/chat"
        headers = {'Content-Type': 'application/json'}
        secret = os.getenv("AGENT_SECRET", "")
        if secret:
            headers["X-Agent-Secret"] = secret
            token = hmac.new(secret.encode(), str(request.env.uid).encode(), hashlib.sha256).hexdigest()
            headers["X-User-Token"] = token
        uid = request.env.uid
        contexto = self._recuperar_contexto(mensaje)

        try:
            respuesta_http = requests.post(url_fastapi, json={"mensaje": mensaje, "user_id": uid, "contexto": contexto}, headers=headers, timeout=30)
            
            if respuesta_http.status_code != 200:
                return {"status": "error", "respuesta": f"Error en FastAPI: {respuesta_http.status_code}"}
                
            respuesta_ia = respuesta_http.json()
            
            if respuesta_ia.get("tipo") == "texto":
                return {"status": "success", "respuesta": respuesta_ia.get("respuesta", "Sin contenido")}
            
            elif respuesta_ia.get("tipo") == "accion":
                accion = respuesta_ia.get("accion")
                parametros = respuesta_ia.get("parametros", {})
                
                # ==========================================
                # MAGIA: Delegamos la ejecución al despachador
                # Le pasamos request.env para mantener la seguridad de sesión
                # ==========================================
                resultado_odoo = procesar_accion_ia(request.env, accion, parametros)
                
                payload_confirmacion = {
                    "mensaje_original": mensaje,
                    "mensaje_ia_seguro": respuesta_ia.get("mensaje_ia_seguro"),
                    "tool_id": respuesta_ia.get("tool_id"),
                    "tool_name": accion,
                    "resultado_odoo": resultado_odoo,
                    "user_id": uid,
                    "contexto": contexto
                }
                
                confirmacion_http = requests.post(os.getenv("FASTAPI_URL", "http://fastapi_ai:8000") + "/api/chat/confirmar", json=payload_confirmacion, headers=headers, timeout=30)
              
                if confirmacion_http.status_code != 200:
                    return {"status": "error", "respuesta": f"FastAPI falló al confirmar: {confirmacion_http.text}"}
                
                respuesta_final = confirmacion_http.json()
                
                return {"status": "success", "respuesta": respuesta_final.get("respuesta", "Acción completada.")}
            
            else:
                return {"status": "error", "respuesta": f"Formato inesperado: {respuesta_ia}"}
                
        except Exception as e:
            return {"status": "error", "respuesta": f"Fallo interno en Odoo: {str(e)}"}