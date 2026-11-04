HERRAMIENTAS_CORRECCIONES = [
    {
        "type": "function",
        "function": {
            "name": "guardar_correccion",
            "description": "Guarda una correccion o feedback del usuario para mejorar futuras respuestas del agente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pregunta": {"type": "string", "description": "Pregunta original del usuario (opcional)"},
                    "correccion": {"type": "string", "description": "Correccion o preferencia indicada por el usuario"}
                },
                "required": ["correccion"]
            }
        }
    }
]