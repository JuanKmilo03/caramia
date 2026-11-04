import os
import json
import redis
from openai import AsyncOpenAI
from datetime import datetime, timedelta
from tools.registry import TODAS_LAS_HERRAMIENTAS

# Memoria a Corto Plazo
redis_host = os.getenv("REDIS_HOST", "localhost")
# decode_responses=True hace que Redis nos devuelva texto (strings) en lugar de bytes
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

client = AsyncOpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url="https://api.groq.com/openai/v1" 
)
MODELO = os.getenv("AI_MODEL", "openai/gpt-oss-20b")

def optimizar_tokens(mensajes, limite=8):
    """Mantiene el System Prompt y los últimos N mensajes, evitando romper lógicas de tools."""
    if len(mensajes) <= limite + 1:
        return mensajes
        
    system_prompt = mensajes[0]
    corte = -limite
    while corte < 0 and mensajes[corte].get("role") == "tool":
        corte -= 1
    # Asegurar que no quedan mensajes 'tool' huérfanos al inicio del bloque
    while corte < 0 and mensajes[corte].get("role") == "tool":
        corte -= 1
    recorte = mensajes[corte:]
    # Eliminar tool messages iniciales sin assistant previo
    while recorte and recorte[0].get("role") == "tool":
        recorte.pop(0)
    return [system_prompt] + recorte

def obtener_historial(user_id: int, contexto: str = ""):
    """Lee el historial desde Redis y actualiza el reloj interno en tiempo real."""
    key = f"chat_historial:{user_id}"
    datos_guardados = redis_client.get(key)
    
    # 1. Pre-calculamos fechas exactas con Python SIEMPRE, sin importar si hay historial o no
    hoy = datetime.now()
    fecha_hoy = hoy.strftime("%Y-%m-%d")
    dia_semana = hoy.strftime("%A")
    
    hace_7_dias = (hoy - timedelta(days=7)).strftime("%Y-%m-%d")
    hace_15_dias = (hoy - timedelta(days=15)).strftime("%Y-%m-%d")
    hace_1_mes = (hoy - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 2. Construimos el System Prompt Dinámico
    system_prompt_dinamico = f"""Eres el asistente inteligente del ERP Cara Mia. Tu objetivo es ayudar a gestionar la base de datos de Odoo mediante las herramientas que tienes conectadas.
    
    CONTEXTO TEMPORAL EXACTO (Usa estrictamente estas fechas si el usuario pide períodos relativos):
    - Hoy ({dia_semana}): {fecha_hoy}
    - Hace 7 días (semana pasada): {hace_7_dias}
    - Hace 15 días (quincena): {hace_15_dias}
    - Hace 1 mes: {hace_1_mes}

    REGLAS DE COMPORTAMIENTO:
    1. NUNCA expongas código JSON o formatos crudos al usuario. Presenta la información de forma natural.
    2. MEMORIA: Si el usuario hace preguntas de seguimiento, revisa el historial para responder sin consultar de nuevo.
    3. REGLA DE ORO (Límites): Solo puedes ejecutar UNA (1) acción de herramienta a la vez. Para peticiones múltiples, ejecuta solo la primera y pregunta si continúas.
    4. USO DE HERRAMIENTAS: Cuando decidas usar una herramienta, NO agregues comentarios, pensamientos ni etiquetas.
    5. NUNCA inventes parámetros obligatorios. Si falta un dato, pregunta.
    6. CONFIRMACION: Antes de ejecutar cualquier accion de creacion, edicion o eliminacion, resume al usuario lo que vas a hacer y pide confirmacion explicita. Solo ejecuta la herramienta cuando el usuario haya confirmado.
    7. Si el usuario corrige informacion o indica una preferencia, usa la herramienta guardar_correccion para recordarlo.
    8. Las respuestas pueden leerse en voz alta: se conciso, evita markdown complejo y listas muy largas.
    """
    
    # 3. Lógica de sobrescritura
    if datos_guardados:
        mensajes = json.loads(datos_guardados)
        # Reemplazamos el primer mensaje (el system prompt congelado) por el dinámico
        if mensajes and mensajes[0].get("role") == "system":
            mensajes[0]["content"] = system_prompt_dinamico
        else:
            mensajes.insert(0, {"role": "system", "content": system_prompt_dinamico})
        return mensajes
    else:
        return [
            {
                "role": "system", 
                "content": system_prompt_dinamico
            }
        ]

def guardar_historial(user_id: int, mensajes: list):
    """Guarda el historial en Redis y le da 24 horas de vida (TTL)."""
    key = f"chat_historial:{user_id}"
    # 86400 segundos = 24 horas. Después de eso, Redis lo borra automáticamente.
    redis_client.setex(key, 86400, json.dumps(mensajes))

async def procesar_chat(mensaje: str, user_id: int, contexto: str = ""):
    mensajes = obtener_historial(user_id, contexto)
    mensajes.append({"role": "user", "content": mensaje})
    
    mensajes = optimizar_tokens(mensajes)

    respuesta = await client.chat.completions.create(
        model=MODELO,
        messages=mensajes,
        tools=TODAS_LAS_HERRAMIENTAS,
        tool_choice="auto" 
    )
    
    mensaje_ia = respuesta.choices[0].message

    if hasattr(mensaje_ia, 'tool_calls') and mensaje_ia.tool_calls:
        tool = mensaje_ia.tool_calls[0]
        
        try:
            argumentos = json.loads(tool.function.arguments)
        except json.JSONDecodeError:
            argumentos = {}
            
        mensaje_ia_seguro = {
            "role": "assistant",
            "content": mensaje_ia.content,
            "tool_calls": [{"id": tool.id, "type": "function", "function": {"name": tool.function.name, "arguments": tool.function.arguments}}]
        }

        mensajes.append(mensaje_ia_seguro)
        guardar_historial(user_id, mensajes)

        return {
            "tipo": "accion",
            "accion": tool.function.name,
            "parametros": argumentos,
            "tool_id": tool.id,
            "mensaje_ia_seguro": mensaje_ia_seguro
        }

    mensajes.append({"role": "assistant", "content": mensaje_ia.content})
    guardar_historial(user_id, mensajes)
    
    return {
        "tipo": "texto",
        "respuesta": mensaje_ia.content
    }

async def confirmar_accion(mensaje_original: str, mensaje_ia_seguro: dict, tool_id: str, tool_name: str, resultado_odoo: str, user_id: int, contexto: str = ""):
    mensajes = obtener_historial(user_id, contexto)
    
    # 1. Agregamos el resultado que devolvió Odoo (el éxito o el error)
    mensajes.append({"role": "tool", "tool_call_id": tool_id, "name": tool_name, "content": str(resultado_odoo)})

    # 2. Creamos una lista temporal solo para esta llamada a Groq
    mensajes_para_groq = mensajes.copy()
    mensajes_para_groq.append({
        "role": "system",
        "content": "El sistema Odoo acaba de devolver el resultado de la acción. Tu ÚNICA tarea ahora es leer ese resultado y explicárselo al usuario de forma natural. NO intentes arreglar el error ni usar herramientas."
    })

    mensajes_para_groq = optimizar_tokens(mensajes_para_groq)

    # 3. Llamamos a Groq PASÁNDOLE LAS HERRAMIENTAS (Obligatorio por validación de la API)
    respuesta_final = await client.chat.completions.create(
        model=MODELO,
        messages=mensajes_para_groq,
        tools=TODAS_LAS_HERRAMIENTAS,
        tool_choice="none"
    )
    
    contenido_final = respuesta_final.choices[0].message.content
    
    # 4. Guardamos en el historial real (la respuesta final, pero sin la regla temporal)
    mensajes.append({"role": "assistant", "content": contenido_final})
    guardar_historial(user_id, mensajes) 
    
    return contenido_final