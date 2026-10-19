import os
import json
from openai import AsyncOpenAI
from entidades import catalogo
from herramientas import TOOLS, ejecutar

client = AsyncOpenAI(
    api_key=os.getenv("AI_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODELO = os.getenv("AI_MODEL", "openai/gpt-oss-20b")

SYSTEM = f"""Eres el asistente del ERP de la fábrica Cara Mia. Tienes acceso al sistema mediante herramientas.
Entidades disponibles:
{catalogo()}

Reglas:
- Para consultar, crear o editar datos usa SIEMPRE las herramientas; no inventes datos.
- Antes de editar o referenciar un registro, búscalo para obtener su 'id'.
- Si falta un dato obligatorio, pídeselo al usuario en vez de inventarlo.
- Si una herramienta devuelve un error, explícalo con claridad al usuario.
- Responde en español, breve y claro."""


async def procesar_chat(mensaje: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": mensaje},
    ]
    try:
        for _ in range(6):
            resp = await client.chat.completions.create(
                model=MODELO, messages=messages, tools=TOOLS, tool_choice="auto"
            )
            msg = resp.choices[0].message

            if not msg.tool_calls:
                return msg.content or "Listo."

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": t.id, "type": "function",
                     "function": {"name": t.function.name, "arguments": t.function.arguments}}
                    for t in msg.tool_calls
                ],
            })

            for t in msg.tool_calls:
                try:
                    args = json.loads(t.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                print(f"[TOOL] {t.function.name} {args}", flush=True)
                resultado = await ejecutar(t.function.name, args)
                print(f"[RESULTADO] {resultado[:200]}", flush=True)
                messages.append({"role": "tool", "tool_call_id": t.id, "content": resultado})

        return "No pude completar la solicitud."
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}", flush=True)
        return "Hubo un error interno al procesar tu solicitud."
