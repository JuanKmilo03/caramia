HERRAMIENTAS_COSTOS = [
    {
        "type": "function",
        "function": {
            "name": "crear_cotizacion_base",
            "description": "Crea una cotización en blanco (o basada en un modelo existente) para presupuestar la fabricación de un zapato.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {"type": "string", "description": "Opcional. Nombre del cliente"},
                    "modelo_existente": {"type": "string", "description": "Opcional. Nombre de una referencia ya creada para copiar sus costos"},
                    "modelo_nuevo": {"type": "string", "description": "Opcional. Si el zapato no existe, el nombre del nuevo diseño"},
                    "tipo_lote": {"type": "string", "enum": ["12", "24"], "description": "Tamaño del lote a cotizar (12 o 24 pares)"},
                    "precio_venta_esperado": {"type": "number", "description": "En cuánto planeamos vender el par de este zapato"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_rentabilidad_cotizacion",
            "description": "Lee una cotización para informar cuánto costarán los materiales, la mano de obra y cuál será la ganancia neta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_cotizacion": {"type": "string", "description": "Ej: COT-001"}
                },
                "required": ["numero_cotizacion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aprobar_cotizacion_a_produccion",
            "description": "Aprueba una cotización y genera automáticamente su orden de producción en la fábrica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_cotizacion": {"type": "string", "description": "Ej: COT-001"}
                },
                "required": ["numero_cotizacion"]
            }
        }
    }
]