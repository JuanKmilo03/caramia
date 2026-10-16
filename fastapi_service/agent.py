import os
import json
from openai import AsyncOpenAI
from odoo_client import odoo_db

client = AsyncOpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url="https://api.groq.com/openai/v1" 
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "consultar_clientes",
            "description": "Consulta la lista de clientes registrados en la fábrica Cara Mia.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_cliente",
            "description": "Crea un nuevo cliente en la base de datos de Odoo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {"type": "string", "description": "Nombre del cliente"},
                    "telefono_cliente": {"type": "string", "description": "Teléfono del cliente"},
                    "direccion": {"type": "string", "description": "Dirección del cliente"},
                    "sello": {"type": "string", "description": "Sello o marca"}
                },
                "required": ["nombre_cliente"]
            }
        }
    }
]

async def procesar_chat(mensaje: str) -> str:
    try:
        # PRIMERA LLAMADA: Tu modelo original
        respuesta = await client.chat.completions.create(
            model="openai/gpt-oss-20b", 
            messages=[
                {
                    "role": "system", 
                    "content": """Eres el asistente del ERP Cara Mia. Tienes acceso real al sistema mediante herramientas.
                    REGLA SUPREMA: Si el usuario te pide crear, agregar o registrar un cliente, ES OBLIGATORIO que uses la función 'crear_cliente' con los datos solicitados. NUNCA digas que no puedes hacerlo."""
                },
                {"role": "user", "content": mensaje}
            ],
            tools=tools,
            tool_choice="auto" 
        )
        
        mensaje_ia = respuesta.choices[0].message

        print("=== RESPUESTA DE LA IA ===", flush=True)
        print(f"Herramientas invocadas: {mensaje_ia.tool_calls}", flush=True)
        print("==========================", flush=True)

        if hasattr(mensaje_ia, 'tool_calls') and mensaje_ia.tool_calls:
            
            # Limpiamos el mensaje de campos ocultos que causan error
            lista_herramientas = []
            for t in mensaje_ia.tool_calls:
                lista_herramientas.append({
                    "id": t.id,
                    "type": "function",
                    "function": {
                        "name": t.function.name,
                        "arguments": t.function.arguments
                    }
                })
                
            mensaje_ia_seguro = {
                "role": "assistant",
                "content": mensaje_ia.content if mensaje_ia.content else "",
                "tool_calls": lista_herramientas
            }
            
            for tool in mensaje_ia.tool_calls:
                
                if tool.function.name == "consultar_clientes":
                    campos = ['cliente_id', 'nombre_cliente', 'telefono_cliente', 'sello']
                    clientes = odoo_db.buscar_datos('cara.mia.cliente', [], campos)
                    datos_string = json.dumps(clientes) if clientes else "No hay clientes en Cara Mia."
                    
                    respuesta_final = await client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            # Le devolvemos su identidad para que no enloquezca
                            {"role": "system", "content": "Eres el asistente de Cara Mia. Resume esta información de forma natural al usuario y NO uses herramientas."},
                            {"role": "user", "content": mensaje},
                            mensaje_ia_seguro, 
                            {"role": "tool", "tool_call_id": tool.id, "name": tool.function.name, "content": datos_string}
                        ]
                    )
                    return respuesta_final.choices[0].message.content

                elif tool.function.name == "crear_cliente":
                    try:
                        argumentos = json.loads(tool.function.arguments)
                    except json.JSONDecodeError:
                        argumentos = {}
                        
                    print(f"Datos a guardar: {argumentos}", flush=True) 
                    
                    valores = {"nombre_cliente": argumentos.get("nombre_cliente", "Cliente Desconocido")}
                    if "telefono_cliente" in argumentos:
                        valores["telefono_cliente"] = argumentos["telefono_cliente"]
                    if "direccion" in argumentos:
                        valores["direccion"] = argumentos["direccion"]
                    if "sello" in argumentos:
                        valores["sello"] = argumentos["sello"]
                
                    nuevo_id = odoo_db.crear_registro('cara.mia.cliente', valores)
                
                    if nuevo_id:
                        datos_string = f"Éxito: Cliente creado en Odoo con ID {nuevo_id}."
                    else:
                        datos_string = "Error: Hubo un problema al guardar en la base de datos de Odoo."
                
                    respuesta_final = await client.chat.completions.create(
                        model="openai/gpt-oss-20b", 
                        messages=[
                            # Instrucción estricta para la confirmación
                            {"role": "system", "content": "Eres el asistente de Cara Mia. El cliente ya fue creado con éxito. Dale un mensaje breve y amable al usuario confirmando la acción. NO uses herramientas ni vuelvas a llamar a crear_cliente."},
                            {"role": "user", "content": mensaje},
                            mensaje_ia_seguro, 
                            {"role": "tool", "tool_call_id": tool.id, "name": tool.function.name, "content": datos_string}
                        ]
                    )
                    return respuesta_final.choices[0].message.content

        return mensaje_ia.content

    except Exception as e:
        print(f"ERROR CRÍTICO: {str(e)}", flush=True)
        return "Hubo un error interno al procesar tu solicitud."