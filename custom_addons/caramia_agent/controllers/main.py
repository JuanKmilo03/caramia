import requests
from odoo import http
from odoo.http import request

# Importamos nuestro Despachador Genérico
from ..ai_actions.dispatcher import procesar_accion_ia

class AgenteController(http.Controller):
    
    @http.route('/caramia/agente', type='http', auth='user')
    def mostrar_pantalla_chat(self, **kw):
        return request.render('caramia_agent.pantalla_chat_ia')

    @http.route('/caramia/chat', type='json', auth='user')
    def enviar_mensaje_ia(self, mensaje):
        url_fastapi = "http://fastapi_ai:8000/api/chat"
        headers = {'Content-Type': 'application/json'}
        uid = request.env.uid

        try:
            respuesta_http = requests.post(url_fastapi, json={"mensaje": mensaje, "user_id": uid}, headers=headers)
            
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
                    "user_id": uid
                }
                
                confirmacion_http = requests.post("http://fastapi_ai:8000/api/chat/confirmar", json=payload_confirmacion, headers=headers)
              
                if confirmacion_http.status_code != 200:
                    return {"status": "error", "respuesta": f"FastAPI falló al confirmar: {confirmacion_http.text}"}
                
                respuesta_final = confirmacion_http.json()
                
                return {"status": "success", "respuesta": respuesta_final.get("respuesta", "Acción completada.")}
            
            else:
                return {"status": "error", "respuesta": f"Formato inesperado: {respuesta_ia}"}
                
        except Exception as e:
            return {"status": "error", "respuesta": f"Fallo interno en Odoo: {str(e)}"}