import os
import json
import redis
from openai import AsyncOpenAI
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
        
    return [system_prompt] + mensajes[corte:]

def obtener_historial(user_id: int):
    """Lee el historial desde Redis o crea uno nuevo si no existe."""
    key = f"chat_historial:{user_id}"
    datos_guardados = redis_client.get(key)
    
    if datos_guardados:
        return json.loads(datos_guardados)
    else:
        return [
            {
                "role": "system", 
                "content": """Eres el asistente del ERP Cara Mia. Recibirás datos desde Odoo.
                REGLAS:
                - Si el usuario pide crear un cliente, usa OBLIGATORIAMENTE 'crear_cliente'.
                - Si piden listar clientes, usa 'consultar_clientes'.
                - Si consultas, y el usuario pide solo "ver clientes", da una lista ÚNICAMENTE con nombres.
                - NUNCA expongas JSON al usuario.
                - Si el usuario pregunta por un cliente específico (ej: "¿Qué sabes de Juan?"), busca en el historial de la conversación si ya consultaste la base de datos recientemente y usa esa información para responder de forma detallada.
                - REGLA DE ORO: Solo puedes ejecutar UNA (1) acción a la vez. Si el usuario te pide crear múltiples registros (ej: 3 clientes), ejecuta la herramienta SOLO para el primero. En tu mensaje final, avísale que creaste el primero y pregúntale si deseas que continúes con el siguiente."""
            }
        ]

def guardar_historial(user_id: int, mensajes: list):
    """Guarda el historial en Redis y le da 24 horas de vida (TTL)."""
    key = f"chat_historial:{user_id}"
    # 86400 segundos = 24 horas. Después de eso, Redis lo borra automáticamente.
    redis_client.setex(key, 86400, json.dumps(mensajes))

async def procesar_chat(mensaje: str, user_id: int):
    mensajes = obtener_historial(user_id)
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
        guardar_historial(user_id, mensajes) # Guardamos el progreso en Redis

        return {
            "tipo": "accion",
            "accion": tool.function.name,
            "parametros": argumentos,
            "tool_id": tool.id,
            "mensaje_ia_seguro": mensaje_ia_seguro
        }

    mensajes.append({"role": "assistant", "content": mensaje_ia.content})
    guardar_historial(user_id, mensajes) # Guardamos el progreso en Redis
    
    return {
        "tipo": "texto",
        "respuesta": mensaje_ia.content
    }

async def confirmar_accion(mensaje_original: str, mensaje_ia_seguro: dict, tool_id: str, tool_name: str, resultado_odoo: str, user_id: int):
    mensajes = obtener_historial(user_id)
    mensajes.append({"role": "tool", "tool_call_id": tool_id, "name": tool_name, "content": resultado_odoo})

    mensajes = optimizar_tokens(mensajes)

    respuesta_final = await client.chat.completions.create(
        model=MODELO,
        messages=mensajes
    )
    
    contenido_final = respuesta_final.choices[0].message.content
    
    mensajes.append({"role": "assistant", "content": contenido_final})
    guardar_historial(user_id, mensajes) # Guardamos el estado final en Redis
    
    return contenido_final