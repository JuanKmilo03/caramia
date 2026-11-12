from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Query, Request, BackgroundTasks
from whatsapp import (
    verificar_token_meta, 
    es_numero_permitido, 
    parsear_mensaje_meta, 
    procesar_mensaje_whatsapp_background
)
from pydantic import BaseModel
from agent import procesar_chat, confirmar_accion
from openai import AsyncOpenAI as _AsyncOpenAI
import os
import io
import time
import hmac
import hashlib
import traceback
import httpx

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "mi_secreto_caramia")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")
AGENT_SECRET = os.getenv("AGENT_SECRET", "")
ALLOWED_PHONE_NUMBER = os.getenv("ALLOWED_PHONE_NUMBER", "")

# Nuevas variables configurables
ODOO_API_URL = os.getenv("ODOO_API_URL")
META_API_VERSION = os.getenv("META_API_VERSION")

AGENT_SECRET = os.getenv("AGENT_SECRET", "")
STT_PROVIDER = os.getenv("STT_PROVIDER", "openai").strip().lower()

# STT: solo proveedor OpenAI (API compatible). Se pueden usar credenciales
# propias para voz con STT_API_KEY / STT_BASE_URL; si no, se reutilizan AI_*.
STT_API_KEY = os.getenv("STT_API_KEY") or os.getenv("AI_API_KEY")
STT_BASE_URL = os.getenv("STT_BASE_URL") or os.getenv("AI_URL")
STT_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
stt_client = (
    _AsyncOpenAI(api_key=STT_API_KEY, base_url=STT_BASE_URL) if STT_API_KEY else None
)

if STT_PROVIDER != "openai":
    print(
        f"[STT] Proveedor '{STT_PROVIDER}' no soportado; se usará OpenAI.",
        flush=True,
    )
    STT_PROVIDER = "openai"
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

@app.get("/")
def read_root():
    return {"status": "El microservicio del agente está corriendo correctamente."}

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


@app.post("/api/stt")
async def stt_endpoint(file: UploadFile = File(...), x_agent_secret: str | None = Header(default=None)):
    _verificar_secret(x_agent_secret)
    try:
        data = await file.read()
        print(f"[STT] filename={file.filename} content_type={file.content_type} size={len(data)}", flush=True)
        if not data:
            raise HTTPException(status_code=400, detail="archivo vacio")
        if STT_PROVIDER != "openai":
            raise HTTPException(status_code=501, detail="Proveedor STT no soportado")
        if stt_client is None:
            raise HTTPException(status_code=500, detail="STT_API_KEY / AI_API_KEY no configurada")
        transcript = await stt_client.audio.transcriptions.create(
            model=STT_MODEL,
            file=(file.filename or "audio.webm", io.BytesIO(data), file.content_type or "audio/webm"),
        )
        texto = transcript.text
        print(f"[STT] texto={texto}", flush=True)
        return {"texto": texto}
    except Exception as e:
        print(f"[STT] ERROR {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# RUTAS DE WHATSAPP
# ==========================================
@app.get("/webhook")
async def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    return verificar_token_meta(hub_mode, hub_challenge, hub_verify_token)

@app.post("/webhook")
async def recibir_whatsapp(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    try:
        datos_mensaje = parsear_mensaje_meta(body)
        if datos_mensaje["valido"]:
            numero_remitente = datos_mensaje["numero"]
            
            if not es_numero_permitido(numero_remitente):
                print(f"🚫 Acceso denegado. Mensaje de: {numero_remitente}", flush=True)
                return {"status": "success"} 
                
            background_tasks.add_task(procesar_mensaje_whatsapp_background, datos_mensaje)
            
        return {"status": "success"}
    except Exception as e:
        print("❌ ERROR EN WEBHOOK:", flush=True)
        return {"status": "ok"}