import os
import hmac
import hashlib
import requests
import json
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

    @http.route('/caramia/stt', type='http', auth='user', methods=['POST'], csrf=False)
    def transcribir_audio(self, **kw):
        import requests as _r
        url = os.getenv("FASTAPI_URL", "http://fastapi_ai:8000") + "/api/stt"
        headers = {}
        secret = os.getenv("AGENT_SECRET", "")
        if secret:
            headers["X-Agent-Secret"] = secret
        try:
            archivo = request.httprequest.files.get('file')
            if not archivo:
                return request.make_response('{"error":"sin archivo"}', headers=[('Content-Type','application/json')], status=400)
            files = {'file': (archivo.filename, archivo.read(), archivo.content_type or 'audio/webm')}
            resp = _r.post(url, files=files, headers=headers, timeout=60)
            return request.make_response(resp.text, headers=[('Content-Type','application/json')], status=resp.status_code)
        except Exception as e:
            return request.make_response('{"error":"%s"}' % str(e), headers=[('Content-Type','application/json')], status=500)

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


    @http.route('/api/agent/action', type='http', auth='public', methods=['POST'], csrf=False)
    def ejecutar_accion_desde_fastapi(self, **kwargs):
        """
        Ruta exclusiva y blindada para recibir comandos desde FastAPI.
        """
        # 1. Barrera de Seguridad: Validar el token interno
        incoming_secret = request.httprequest.headers.get('X-Agent-Secret')
        expected_secret = os.getenv("AGENT_SECRET", "")
        
        if not expected_secret or incoming_secret != expected_secret:
            return request.make_response(
                json.dumps({"error": "Acceso Denegado: Credenciales inválidas"}), 
                headers=[('Content-Type','application/json')], 
                status=401
            )
            
        try:
            # 2. Leer la petición enviada por FastAPI
            raw_data = request.httprequest.get_data(as_text=True)
            data = json.loads(raw_data)
            tool_name = data.get('tool_name')
            parameters = data.get('parameters', {})
            
            # 3. MAGIA: Ejecutar el despachador
            # Utilizamos sudo() porque la petición de WhatsApp entra de forma 'public'
            # sudo() permite ejecutar la acción a nivel de base de datos de manera segura
            resultado_odoo = procesar_accion_ia(request.env(su=True), tool_name, parameters)
            
            # 4. Devolver el resultado a FastAPI
            return request.make_response(
                json.dumps({"status": "success", "resultado": str(resultado_odoo)}), 
                headers=[('Content-Type','application/json')], 
                status=200
            )
            
        except Exception as e:
            return request.make_response(
                json.dumps({"status": "error", "error": str(e)}), 
                headers=[('Content-Type','application/json')], 
                status=500
            )