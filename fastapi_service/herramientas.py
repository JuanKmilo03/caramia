import asyncio
import json
from entidades import ENTIDADES
from odoo_client import odoo_db

NOMBRES = list(ENTIDADES.keys())


def construir_tools():
    tools = [
        {"type": "function", "function": {
            "name": "buscar",
            "description": "Consulta registros de una entidad. Úsalo también para obtener IDs antes de crear o editar.",
            "parameters": {"type": "object", "properties": {
                "entidad": {"type": "string", "enum": NOMBRES},
                "filtros": {
                    "type": "array",
                    "description": 'Lista de [campo, operador, valor]. Operadores: =, !=, >, <, >=, <=, ilike. '
                                   'Ej: [["nombre_empleado","ilike","juan"]]',
                    "items": {"type": "array", "items": {}},
                },
                "limite": {"type": "integer", "description": "Máximo de registros (por defecto 20)"},
            }, "required": ["entidad"]}}},
        {"type": "function", "function": {
            "name": "crear",
            "description": "Crea un registro nuevo. Si faltan datos obligatorios, pídeselos al usuario.",
            "parameters": {"type": "object", "properties": {
                "entidad": {"type": "string", "enum": NOMBRES},
                "valores": {"type": "object", "description": "Diccionario campo: valor"},
            }, "required": ["entidad", "valores"]}}},
        {"type": "function", "function": {
            "name": "editar",
            "description": "Modifica un registro existente usando su ID interno ('id').",
            "parameters": {"type": "object", "properties": {
                "entidad": {"type": "string", "enum": NOMBRES},
                "id": {"type": "integer"},
                "valores": {"type": "object"},
            }, "required": ["entidad", "id", "valores"]}}},
    ]
    if any("borrar" in c["permisos"] for c in ENTIDADES.values()):
        tools.append({"type": "function", "function": {
            "name": "borrar",
            "description": "Elimina un registro por ID. Solo si el usuario lo pidió explícitamente.",
            "parameters": {"type": "object", "properties": {
                "entidad": {"type": "string", "enum": NOMBRES},
                "id": {"type": "integer"},
            }, "required": ["entidad", "id"]}}})
    return tools


TOOLS = construir_tools()


def _cfg(entidad, permiso):
    cfg = ENTIDADES.get(entidad)
    if not cfg:
        raise ValueError(f"Entidad desconocida: {entidad}")
    if permiso not in cfg["permisos"]:
        raise PermissionError(f"No está permitido '{permiso}' en '{entidad}'.")
    return cfg


def _solo_escribibles(cfg, valores):
    return {k: v for k, v in (valores or {}).items() if k in cfg["campos_escritura"]}


def t_buscar(entidad, filtros=None, limite=20):
    cfg = _cfg(entidad, "leer")
    permitidos = set(cfg["campos_lectura"])
    dominio = [f for f in (filtros or []) if isinstance(f, list) and len(f) == 3 and f[0] in permitidos]
    datos = odoo_db.buscar_datos(cfg["modelo"], dominio, cfg["campos_lectura"], min(limite or 20, 50))
    return json.dumps(datos, default=str, ensure_ascii=False) if datos else "Sin resultados."


def t_crear(entidad, valores):
    cfg = _cfg(entidad, "crear")
    valores = _solo_escribibles(cfg, valores)
    faltan = [c for c in cfg["requeridos"] if c not in valores]
    if faltan:
        return f"Faltan campos obligatorios: {faltan}. Pídeselos al usuario (o búscalos si son IDs)."
    nuevo_id = odoo_db.crear_registro(cfg["modelo"], valores)
    return f"Creado con id {nuevo_id}."


def t_editar(entidad, id, valores):
    cfg = _cfg(entidad, "editar")
    valores = _solo_escribibles(cfg, valores)
    if not valores:
        return "No hay campos válidos para modificar."
    odoo_db.actualizar_registro(cfg["modelo"], id, valores)
    return f"Registro {id} actualizado."


def t_borrar(entidad, id):
    cfg = _cfg(entidad, "borrar")
    odoo_db.borrar_registro(cfg["modelo"], id)
    return f"Registro {id} eliminado."


FUNCIONES = {"buscar": t_buscar, "crear": t_crear, "editar": t_editar, "borrar": t_borrar}


async def ejecutar(nombre, args):
    try:
        # to_thread: XML-RPC es bloqueante y frenaría FastAPI
        return await asyncio.to_thread(FUNCIONES[nombre], **args)
    except Exception as e:
        return f"Error: {e}"
