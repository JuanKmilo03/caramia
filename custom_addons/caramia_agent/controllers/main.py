import requests
import json
from odoo import http
from odoo.http import request

class AgenteController(http.Controller):
    
    # 1. RUTA PARA MOSTRAR LA INTERFAZ VISUAL DEL CHAT
    @http.route('/caramia/agente', type='http', auth='user')
    def mostrar_pantalla_chat(self, **kw):
        # Llama a la plantilla XML que crearemos a continuación
        return request.render('caramia_agent.pantalla_chat_ia')

    # 2. RUTA PARA ENVIAR Y RECIBIR MENSAJES DE LA IA
    @http.route('/caramia/chat', type='json', auth='user')
    def enviar_mensaje_ia(self, mensaje):
        url_fastapi = "http://fastapi_ai:8000/api/chat"
        payload = {"mensaje": mensaje, "user_id": request.env.uid}
        headers = {'Content-Type': 'application/json'}
        
        try:
            respuesta = requests.post(url_fastapi, data=json.dumps(payload), headers=headers)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return {"status": "success", "respuesta": datos.get("respuesta", "Sin respuesta")}
            return {"status": "error", "respuesta": "Error procesando en FastAPI."}
        except Exception as e:
            return {"status": "error", "respuesta": str(e)}