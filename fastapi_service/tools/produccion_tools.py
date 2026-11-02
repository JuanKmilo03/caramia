HERRAMIENTAS_PRODUCCION = [
    {
        "type": "function",
        "function": {
            "name": "crear_orden_produccion",
            "description": "Crea una nueva Orden de Producción para fabricar zapatos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {"type": "string", "description": "Nombre del cliente al que se le fabrica"},
                    "sello": {"type": "string", "description": "El sello o marca registrada que el cliente usa en su calzado. Es obligatorio."},
                    "nombre_referencia": {"type": "string", "description": "Nombre de la referencia o modelo de zapato a fabricar"},
                    "color": {"type": "string", "description": "Color del calzado"},
                    "material": {"type": "string", "description": "Material principal"},
                    "tallas": {
                        "type": "object", 
                        "description": "Diccionario con las tallas y la cantidad de pares. Ej: {'35': 12, '37': 6}"
                    }
                },
                "required": ["nombre_cliente", "sello", "nombre_referencia", "tallas"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_ordenes_produccion",
            "description": "Consulta la lista de órdenes de producción actuales, su estado y total de pares.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cambiar_estado_orden_produccion",
            "description": "Cambia el estado de una orden de producción. Permite mover la orden libremente entre 'draft' (Borrador), 'in_progress' (En Proceso), 'stopped' (Detenido) o 'canceled' (Cancelado). IMPORTANTE: No tienes permiso para finalizar ('done') una orden. Si una orden ya está Cancelada o Finalizada, es un estado definitivo y no se puede alterar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_orden": {"type": "string", "description": "El código de la orden (Ej: OP-0001)"},
                    "nuevo_estado": {
                        "type": "string",
                        "enum": ["draft", "in_progress", "stopped", "canceled"],
                        "description": "El estado técnico destino al que se quiere mover la orden."
                    }
                },
                "required": ["numero_orden", "nuevo_estado"]
            }
        }
    
    }
]