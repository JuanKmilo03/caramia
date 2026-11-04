HERRAMIENTAS_REFERENCIAS = [
    {
        "type": "function",
        "function": {
            "name": "crear_referencia",
            "description": "Crea una nueva Referencia (modelo de zapato) en el sistema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_modelo": {"type": "string", "description": "Nombre del diseño o modelo del zapato"},
                    "precio_venta_sugerido": {"type": "number", "description": "Precio de venta al público sugerido"},
                    "descripcion": {"type": "string", "description": "Detalles o notas sobre el diseño"}
                },
                "required": ["nombre_modelo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_referencia",
            "description": "Busca una referencia por su nombre y devuelve sus costos de producción, estado y precio sugerido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_modelo": {"type": "string", "description": "Nombre de la referencia a buscar"}
                },
                "required": ["nombre_modelo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "editar_estado_referencia",
            "description": "Cambia el estado de una referencia (activo/inactivo) o actualiza su precio sugerido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_modelo": {"type": "string", "description": "Nombre de la referencia a editar"},
                    "nuevo_estado": {"type": "string", "enum": ["activo", "inactivo"], "description": "Opcional. Activar o inactivar."},
                    "nuevo_precio": {"type": "number", "description": "Opcional. Nuevo precio de venta sugerido."}
                },
                "required": ["nombre_modelo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "eliminar_referencia",
            "description": "Elimina una referencia del sistema. Fallará si la referencia ya tiene órdenes de producción asociadas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_modelo": {"type": "string", "description": "Nombre de la referencia a borrar"},
                    "confirmado": {"type": "boolean", "description": "Bandera de seguridad. Enviar true solo si el usuario confirmó explícitamente."}
                },
                "required": ["nombre_modelo"]
            }
        }
    }
]