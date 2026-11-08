import os
import io
import httpx
import traceback
from fastapi import HTTPException
from openai import AsyncOpenAI as _AsyncOpenAI
from agent import procesar_chat, confirmar_accion

# ==========================================
# 1. CONFIGURACIÓN Y VARIABLES
# ==========================================
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")
META_API_VERSION = os.getenv("META_API_VERSION", "v18.0")
ALLOWED_PHONE_NUMBER = os.getenv("ALLOWED_PHONE_NUMBER", "")

ODOO_API_URL = os.getenv("ODOO_API_URL")
AGENT_SECRET = os.getenv("AGENT_SECRET", "")

# Configuración STT Genérica (Nube)
OPENAI_API_KEY = os.getenv("AI_API_KEY")
AI_URL = os.getenv("AI_URL")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3")
stt_client = _AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=AI_URL) if OPENAI_API_KEY else None

# ==========================================
# 2. FUNCIONES DE APOYO Y VALIDACIÓN
# ==========================================
def verificar_token_meta(hub_mode: str, hub_challenge: str, hub_verify_token: str):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Error de validación")

def es_numero_permitido(numero: str) -> bool:
    if ALLOWED_PHONE_NUMBER and numero != ALLOWED_PHONE_NUMBER:
        return False
    return True

def parsear_mensaje_meta(body: dict) -> dict:
    try:
        entrada = body['entry'][0]['changes'][0]['value']
        if 'messages' in entrada:
            mensaje_wa = entrada['messages'][0]
            return {
                "valido": True,
                "numero": mensaje_wa['from'],
                "tipo": mensaje_wa.get('type'),
                "texto": mensaje_wa['text']['body'] if mensaje_wa.get('type') == 'text' else "",
                "media_id": mensaje_wa['audio']['id'] if mensaje_wa.get('type') == 'audio' else ""
            }
    except Exception:
        pass
    return {"valido": False}

async def ejecutar_accion_odoo(accion: str, parametros: dict) -> str:
    headers = {"Content-Type": "application/json", "X-Agent-Secret": AGENT_SECRET}
    payload = {"tool_name": accion, "parameters": parametros}
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            respuesta = await client.post(ODOO_API_URL, json=payload, headers=headers)
            if respuesta.status_code != 200:
                return f"El ERP falló con error: {respuesta.text}"
            
            data = respuesta.json()
            if data.get("status") == "success":
                return data.get("resultado", "Acción completada.")
            else:
                return f"Error en Odoo: {data.get('error', 'Desconocido')}"
    except Exception as e:
        print(f"❌ Error de red con Odoo: {e}", flush=True)
        return "El sistema ERP se encuentra inaccesible en este momento."

# ==========================================
# 3. MANEJO DE AUDIO Y META (WHATSAPP)
# ==========================================
async def descargar_audio_whatsapp(media_id: str) -> bytes:
    url_info = f"https://graph.facebook.com/{META_API_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        res_info = await client.get(url_info, headers=headers)
        res_info.raise_for_status()
        media_url = res_info.json()["url"]
        
        res_audio = await client.get(media_url, headers=headers)
        res_audio.raise_for_status()
        return res_audio.content

async def enviar_mensaje_whatsapp(telefono_destino: str, texto: str):
    url = f"https://graph.facebook.com/{META_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": telefono_destino, "type": "text", "text": {"body": str(texto)}}
    
    async with httpx.AsyncClient() as client:
        respuesta = await client.post(url, headers=headers, json=payload)
        if respuesta.status_code != 200:
            print(f"❌ ERROR DE META AL ENVIAR: {respuesta.text}", flush=True)

async def transcribir_audio_interno(audio_bytes: bytes) -> str:
    print(f"🎙️ Iniciando transcripción ({len(audio_bytes)} bytes)...", flush=True)
    if stt_client is None:
        raise Exception("OPENAI_API_KEY no configurada para STT")
        
    transcript = await stt_client.audio.transcriptions.create(
        model=WHISPER_MODEL,
        file=("audio.ogg", io.BytesIO(audio_bytes), "audio/ogg"),
    )
    return transcript.text

# ==========================================
# 4. ORQUESTADOR PRINCIPAL (BACKGROUND TASK)
# ==========================================
async def procesar_mensaje_whatsapp_background(datos_mensaje: dict):
    try:
        numero_remitente = datos_mensaje["numero"]
        tipo_mensaje = datos_mensaje["tipo"]
        texto_recibido = datos_mensaje["texto"]
        
        if tipo_mensaje == 'text':
            print(f"📥 TEXTO RECIBIDO DE {numero_remitente}: {texto_recibido}", flush=True)
        elif tipo_mensaje == 'audio':
            print(f"🎙️ AUDIO RECIBIDO DE {numero_remitente}. Descargando...", flush=True)
            audio_bytes = await descargar_audio_whatsapp(datos_mensaje["media_id"])
            texto_recibido = await transcribir_audio_interno(audio_bytes)
            print(f"📝 AUDIO TRANSCRITO: {texto_recibido}", flush=True)
        else:
            return 

        # IA Y ODOO
        respuesta_ia = await procesar_chat(texto_recibido, user_id=numero_remitente, contexto="")
        
        if isinstance(respuesta_ia, dict):
            if respuesta_ia.get("tipo") == "texto":
                texto_a_enviar = respuesta_ia.get("respuesta", "")
            elif respuesta_ia.get("tipo") == "accion":
                accion = respuesta_ia["accion"]
                parametros = respuesta_ia.get("parametros", {})
                
                print(f"⚙️ EJECUTANDO EN ODOO: {accion}", flush=True)
                resultado_odoo = await ejecutar_accion_odoo(accion, parametros)
                
                texto_a_enviar = await confirmar_accion(
                    mensaje_original=texto_recibido,
                    mensaje_ia_seguro=respuesta_ia["mensaje_ia_seguro"],
                    tool_id=respuesta_ia["tool_id"],
                    tool_name=accion,
                    resultado_odoo=resultado_odoo,
                    user_id=numero_remitente,
                    contexto=""
                )
            else:
                texto_a_enviar = str(respuesta_ia)
        else:
            texto_a_enviar = str(respuesta_ia)
            
        await enviar_mensaje_whatsapp(numero_remitente, texto_a_enviar)
        
    except Exception as e:
        print(f"❌ ERROR EN BACKGROUND TASK: {e}", flush=True)
        traceback.print_exc()