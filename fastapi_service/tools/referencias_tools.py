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
            "description": "Busca una referencia por su nombre. Si no se indica nombre, devuelve todas las referencias existentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_modelo": {"type": "string", "description": "Nombre de la referencia a buscar. Omitir para listar todas las referencias."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "editar_referencia",
            "description": "Edita una referencia. IMPORTANTE: Para cambiar las labores al 'precio sugerido 1' o 'precio sugerido 2', SOLO envía el parámetro 'tipo_tarifa_header' como '1' o '2', Odoo hará el resto automáticamente. NO preguntes por labores individuales a menos que el usuario pida precios 'manuales'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_modelo": {
                        "type": "string", 
                        "description": "Nombre de la referencia a editar (ej: zapatico1)"
                    },
                    "tipo_tarifa_header": {
                        "type": "string", 
                        "enum": ["manual", "1", "2"], 
                        "description": "Obligatorio si se cambian los precios de las labores. Usa '1' para sugerido 1, '2' para sugerido 2, o 'manual'. Al usar '1' o '2' NO necesitas enviar ni pedir los precios individuales de las labores."
                    },
                    "precio_venta_sugerido": {
                        "type": "number", 
                        "description": "Precio final de venta del zapato."
                    },
                    "nuevas_tarifas_labores": {
                        "type": "object",
                        "description": "SOLO usar si tipo_tarifa_header es 'manual'. Diccionario con los nombres de labor y sus precios. NUNCA lo pidas si el usuario quiere sugerido 1 o 2.",
                        "additionalProperties": {"type": "number"}
                    }
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