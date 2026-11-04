HERRAMIENTAS_CATALOGOS = [
    {
        "type": "function",
        "function": {
            "name": "crear_tipo_labor",
            "description": "Crea una nueva labor de producción (ej: Corte, Costura, Soladura) en el catálogo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la labor"},
                    "tarifa_normal": {"type": "number", "description": "Precio que se paga por la tarifa normal"},
                    "tarifa_especial": {"type": "number", "description": "Precio que se paga si la tarifa es compleja/especial"}
                },
                "required": ["nombre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_labores",
            "description": "Consulta la lista de todas las labores de producción registradas y sus tarifas.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
{
        "type": "function",
        "function": {
            "name": "actualizar_labor",
            "description": "Modifica la información de un tipo de labor existente. Solo debes enviar los campos que el usuario te pidió cambiar explícitamente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_actual": {"type": "string", "description": "El nombre actual de la labor que se desea modificar (Ej: 'Corte')."},
                    "nuevo_nombre": {"type": "string", "description": "El nuevo nombre para la labor. (Omitir si no se cambia)."},
                    "tarifa_normal": {"type": "number", "description": "Nueva tarifa normal o pago base. (Omitir si no se cambia)."},
                    "tarifa_especial": {"type": "number", "description": "Nueva tarifa especial o compleja. (Omitir si no se cambia)."}
                },
                "required": ["nombre_actual"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "borrar_labor",
            "description": "Elimina permanentemente una labor del sistema. Requiere confirmación de seguridad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la labor a eliminar."},
                    "confirmado": {
                        "type": "boolean",
                        "description": "Bandera de seguridad. SIEMPRE envíalo como false en el primer intento. Solo envíalo como true si ya le preguntaste al usuario y este te dio su confirmación explícita para borrarla."
                    }
                },
                "required": ["nombre"]
            }
        }
    },



    {
        "type": "function",
        "function": {
            "name": "crear_insumo",
            "description": "Crea un nuevo material o insumo en el catálogo de inventario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del material (ej: Cuero Napa Negro)"},
                    "tipo_componente": {"type": "string", "description": "Categoría (ej: Cuero, Suela, Hilo, Pegante)"},
                    "unidad_medida": {"type": "string", "enum": ["cm", "mts", "pares", "und"], "description": "Unidad de medida permitida"},
                    "costo_referencia": {"type": "number", "description": "Costo base del insumo"},
                    "stock_minimo": {"type": "number", "description": "Cantidad mínima para alertas"}
                },
                "required": ["nombre", "tipo_componente", "unidad_medida"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_insumos",
            "description": "Busca insumos en el catálogo para ver su costo, unidad de medida y stock actual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del insumo a buscar. Déjalo vacío para listar todos."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_insumo",
            "description": "Modifica la información de un insumo o material existente. Solo envía los datos que el usuario solicitó cambiar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_actual": {"type": "string", "description": "El nombre actual del insumo a modificar."},
                    "nuevo_nombre": {"type": "string", "description": "Nuevo nombre del insumo. (Omitir si no se cambia)."},
                    "tipo_componente": {"type": "string", "description": "Nueva categoría o tipo del componente. (Omitir si no se cambia)."},
                    "unidad_medida": {"type": "string", "description": "Nueva unidad de medida, ej: 'Metros', 'Pares'. (Omitir si no se cambia)."},
                    "costo_referencia": {"type": "number", "description": "Nuevo costo de referencia. (Omitir si no se cambia)."},
                    "stock_minimo": {"type": "number", "description": "Nuevo límite de stock mínimo. (Omitir si no se cambia)."}
                },
                "required": ["nombre_actual"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "borrar_insumo",
            "description": "Elimina permanentemente un insumo del catálogo. Requiere confirmación de seguridad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del insumo a eliminar."},
                    "confirmado": {
                        "type": "boolean",
                        "description": "Bandera de seguridad. SIEMPRE envíalo como false en el primer intento. Solo envíalo como true si ya validaste y el usuario confirmó explícitamente que desea borrarlo."
                    }
                },
                "required": ["nombre"]
            }
        }
    }
]