HERRAMIENTAS_TRACKING = [
    {
        "type": "function",
        "function": {
            "name": "consultar_progreso_orden",
            "description": "Consulta el estado actual de una orden de producción específica, su porcentaje de avance, y en qué labor está trabajando actualmente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo_orden": {"type": "string", "description": "Código de la orden. Ej: PROD-001"}
                },
                "required": ["codigo_orden"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_tablero_produccion",
            "description": "Obtiene un resumen global de toda la fábrica: cuántas órdenes hay activas, cuántas están atrasadas/estancadas y el volumen de pares de la semana.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_ordenes_estancadas",
            "description": "Busca y lista todas las órdenes de producción que el sistema ha marcado como 'estancadas' (sin avance por muchos días).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cambiar_estado_orden_manual",
            "description": "Permite pausar (Detener) o reanudar (En Proceso) una orden de producción manualmente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo_orden": {"type": "string", "description": "Código de la orden"},
                    "accion": {"type": "string", "enum": ["detener", "reanudar"], "description": "Acción a realizar"}
                },
                "required": ["codigo_orden", "accion"]
            }
        }
    }
]