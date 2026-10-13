import os
import json
from openai import AsyncOpenAI
from odoo_client import odoo_db

# Configuramos el cliente. Si usas Groq, la base_url cambia. Si usas OpenAI, borra base_url.
client = AsyncOpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url="https://api.groq.com/openai/v1" 
)

# Definimos las herramientas (Function Calling)
herramientas = [
    {
        "type": "function",
        "function": {
            "name": "consultar_clientes",
            "description": "Obtiene una lista de clientes registrados en el sistema de la fábrica.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

async def procesar_chat(mensaje: str) -> str:
    
    respuesta = await client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system",
            "content": """Eres el asistente virtual de la fábrica de calzado Cara Mia. 
            Tu objetivo es ayudar a los empleados respondiendo de forma natural, cálida y conversacional. 
            Reglas estrictas:
            1. NUNCA uses tablas Markdown para responder, a menos que el usuario pida explícitamente una 'tabla' o una 'lista detallada'.
            2. Responde en párrafos cortos, como si estuvieras chateando por WhatsApp.
            3. No muestres IDs internos de la base de datos a menos que sea estrictamente necesario.
            4. Si encuentras un cliente, preséntalo de forma fluida (ej: 'Encontré al cliente Andepsito, su teléfono es 33333 y su sello es 67.')."""
            },
            {"role": "user", "content": mensaje}
        ],
        tools=herramientas,
        tool_choice="auto"
    )
    
    mensaje_ia = respuesta.choices[0].message

    if mensaje_ia.tool_calls:
        for tool in mensaje_ia.tool_calls:
            if tool.function.name == "consultar_clientes":

                campos = ['cliente_id', 'nombre_cliente', 'telefono_cliente', 'sello']
                
                clientes = odoo_db.buscar_datos('cara.mia.cliente', [], campos)
                
                datos_string = json.dumps(clientes) if clientes else "No hay clientes en Cara Mia."
                
                respuesta_final = await client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "user", "content": mensaje},
                        mensaje_ia,
                        {"role": "tool", "tool_call_id": tool.id, "name": tool.function.name, "content": datos_string}
                    ]
                )
                return respuesta_final.choices[0].message.content

    # 3. Si es una conversación normal, devuelve el texto
    return mensaje_ia.content