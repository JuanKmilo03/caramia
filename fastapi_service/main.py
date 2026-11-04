from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import procesar_chat, confirmar_accion
import traceback


app = FastAPI(title="API Agente Cara Mia")

class ChatRequest(BaseModel):
    mensaje: str
    user_id: int

class ConfirmacionRequest(BaseModel):
    mensaje_original: str
    mensaje_ia_seguro: dict
    tool_id: str
    tool_name: str
    resultado_odoo: str
    user_id: int

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Devuelve el diccionario directamente (texto o acción)
        return await procesar_chat(request.mensaje, request.user_id)
    except Exception as e:
        # --- NUEVAS LÍNEAS PARA VER EL ERROR REAL ---
        print("===== ERROR FATAL EN FASTAPI =====")
        traceback.print_exc()
        print("==================================")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/confirmar")
async def confirmar_endpoint(req: ConfirmacionRequest):
    try:
        # Devuelve la frase final de éxito
        texto_final = await confirmar_accion(
            req.mensaje_original, req.mensaje_ia_seguro, req.tool_id, req.tool_name, req.resultado_odoo, req.user_id
        )
        return {"tipo": "texto", "respuesta": texto_final}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "El microservicio del agente está corriendo correctamente."}