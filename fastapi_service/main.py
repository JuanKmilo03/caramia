from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from agent import procesar_chat, confirmar_accion
import os
import time
import hmac
import hashlib
import traceback

AGENT_SECRET = os.getenv("AGENT_SECRET", "")
_RATE_LIMIT = {}
_RATE_WINDOW = 60
_RATE_MAX = 30

def _check_rate_limit(user_id: int):
    now = time.time()
    bucket = _RATE_LIMIT.setdefault(user_id, [])
    bucket[:] = [t for t in bucket if now - t < _RATE_WINDOW]
    if len(bucket) >= _RATE_MAX:
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes")
    bucket.append(now)


app = FastAPI(title="API Agente Cara Mia")

class ChatRequest(BaseModel):
    mensaje: str
    user_id: int
    contexto: str = ""
    contexto: str = ""

class ConfirmacionRequest(BaseModel):
    mensaje_original: str
    mensaje_ia_seguro: dict
    tool_id: str
    tool_name: str
    resultado_odoo: str
    user_id: int
    contexto: str = ""

def _verificar_secret(x_agent_secret: str | None):
    if AGENT_SECRET and x_agent_secret != AGENT_SECRET:
        raise HTTPException(status_code=401, detail="No autorizado")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, x_agent_secret: str | None = Header(default=None), x_user_token: str | None = Header(default=None)):
    _verificar_secret(x_agent_secret)
    _check_rate_limit(request.user_id)
    if AGENT_SECRET and x_user_token:
        esperado = hmac.new(AGENT_SECRET.encode(), str(request.user_id).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperado, x_user_token):
            raise HTTPException(status_code=401, detail="Usuario no valido")
    try:
        # Devuelve el diccionario directamente (texto o acción)
        return await procesar_chat(request.mensaje, request.user_id, request.contexto)
    except Exception as e:
        # --- NUEVAS LÍNEAS PARA VER EL ERROR REAL ---
        print("===== ERROR FATAL EN FASTAPI =====")
        traceback.print_exc()
        print("==================================")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/confirmar")
async def confirmar_endpoint(req: ConfirmacionRequest, x_agent_secret: str | None = Header(default=None), x_user_token: str | None = Header(default=None)):
    _verificar_secret(x_agent_secret)
    _check_rate_limit(req.user_id)
    if AGENT_SECRET and x_user_token:
        esperado = hmac.new(AGENT_SECRET.encode(), str(req.user_id).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperado, x_user_token):
            raise HTTPException(status_code=401, detail="Usuario no valido")
    try:
        # Devuelve la frase final de éxito
        texto_final = await confirmar_accion(
            req.mensaje_original, req.mensaje_ia_seguro, req.tool_id, req.tool_name, req.resultado_odoo, req.user_id, req.contexto
        )
        return {"tipo": "texto", "respuesta": texto_final}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "El microservicio del agente está corriendo correctamente."}