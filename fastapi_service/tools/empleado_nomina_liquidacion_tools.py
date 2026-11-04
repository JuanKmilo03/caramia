HERRAMIENTAS_OPERACIONES = [
    {
        "type": "function",
        "function": {
            "name": "registrar_tiquete_trabajo",
            "description": "ÚSALA SIEMPRE que el usuario pida 'crear un ticket', 'asignar ticket' o 'registrar trabajo' de una orden a un empleado. Puedes recibir varias órdenes a la vez.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_empleado": {"type": "string", "description": "Nombre o cédula del operario"},
                    "codigo_orden": {"type": "string", "description": "El código de la orden, o varias órdenes separadas por coma. Ej: OP-0006, OP-0002"}
                },
                "required": ["nombre_empleado", "codigo_orden"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_nomina",
            "description": "Calcula y genera la pre-nómina de los empleados en un rango de fechas. Agrupa sus tiquetes pendientes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha de inicio (YYYY-MM-DD)"},
                    "fecha_fin": {"type": "string", "description": "Fecha de fin (YYYY-MM-DD)"}
                },
                "required": ["fecha_inicio", "fecha_fin"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_nomina",
            "description": "Modifica las fechas de una nómina existente en borrador o en proceso.",
            "parameters": {
                "type": "object",
                "properties": {
                    "referencia_nomina": {"type": "string", "description": "El código de la nómina a actualizar. Ej: NOM-001"},
                    "nueva_fecha_inicio": {"type": "string", "description": "Nueva fecha de inicio (YYYY-MM-DD). Omitir si no cambia."},
                    "nueva_fecha_fin": {"type": "string", "description": "Nueva fecha de fin (YYYY-MM-DD). Omitir si no cambia."}
                },
                "required": ["referencia_nomina"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "borrar_nomina",
            "description": "Elimina permanentemente una nómina del sistema. Requiere confirmación de seguridad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "referencia_nomina": {"type": "string", "description": "El código de la nómina a eliminar. Ej: NOM-001"},
                    "confirmado": {
                        "type": "boolean",
                        "description": "Bandera de seguridad. SIEMPRE envíalo como false en el primer intento. Solo envíalo como true si el usuario confirmó explícitamente."
                    }
                },
                "required": ["referencia_nomina"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_liquidacion",
            "description": "Ejecuta el cálculo masivo de liquidación (fondo de reserva 0.22%) para todos los empleados de la fábrica.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_liquidacion",
            "description": "Modifica las observaciones de un documento de liquidación que está en borrador.",
            "parameters": {
                "type": "object",
                "properties": {
                    "referencia_liquidacion": {"type": "string", "description": "El código de la liquidación a modificar. Ej: LIQ-001"},
                    "observaciones": {"type": "string", "description": "Nuevas observaciones o notas. Omitir si no hay cambios."}
                },
                "required": ["referencia_liquidacion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "borrar_liquidacion",
            "description": "Elimina permanentemente una liquidación. Solo se permite si está en borrador. Requiere confirmación de seguridad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "referencia_liquidacion": {"type": "string", "description": "El código de la liquidación a eliminar. Ej: LIQ-001"},
                    "confirmado": {
                        "type": "boolean",
                        "description": "Bandera de seguridad. SIEMPRE envíalo como false en el primer intento. Solo envíalo como true si el usuario confirmó."
                    }
                },
                "required": ["referencia_liquidacion"]
            }
        }
    }
]