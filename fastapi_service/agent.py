import os
import json
from openai import AsyncOpenAI
from odoo_client import odoo_db
from dotenv import load_dotenv

load_dotenv()

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
            {"role": "system", "content": "Eres el asistente inteligente de la fábrica de calzado Cara Mia. Ayudas a los empleados consultando información del ERP de forma concisa."},
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