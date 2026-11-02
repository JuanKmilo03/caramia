HERRAMIENTAS_FACTURACION = [
    {
        "type": "function",
        "function": {
            "name": "crear_factura",
            "description": "Crea una nueva factura o remisión en estado borrador, asociando las órdenes de producción al cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {"type": "string", "description": "Nombre del cliente a facturar"},
                    "forma_pago": {"type": "string", "enum": ["contado", "credito"], "description": "Tipo de pago de la factura"},
                    "fecha_vencimiento": {"type": "string", "description": "Fecha límite de pago (YYYY-MM-DD)"},
                    "ordenes_produccion": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de códigos de las órdenes. Ej: ['PROD-001', 'PROD-002']. Puedes enviar un arreglo explícito ['TODAS'] si el usuario pide facturar TODAS las órdenes finalizadas del cliente."
                    }
                },
                "required": ["nombre_cliente", "forma_pago", "fecha_vencimiento", "ordenes_produccion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_factura_borrador",
            "description": "Modifica la información de una factura que aún está en estado borrador. Sirve para cambiar la fecha de vencimiento o para agregar/quitar órdenes de producción específicas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_factura": {"type": "string", "description": "El número de la factura a actualizar (Ej: FAC-001)"},
                    "fecha_vencimiento": {"type": "string", "description": "Nueva fecha límite de pago (YYYY-MM-DD). Omitir si no se desea cambiar."},
                    "ordenes_agregar": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de códigos de órdenes para agregar a la factura. Ej: ['PROD-003']. Omitir si no hay."
                    },
                    "ordenes_quitar": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de códigos de órdenes para quitar de la factura. Ej: ['PROD-001']. Omitir si no hay."
                    }
                },
                "required": ["numero_factura"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emitir_factura",
            "description": "Pasa una factura de estado borrador a 'Emitida', lo que crea automáticamente la cuenta de cobro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_factura": {"type": "string", "description": "El número de la factura a emitir (Ej: FAC-001)"}
                },
                "required": ["numero_factura"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_factura",
            "description": "Busca una factura específica para ver su total, su saldo y qué órdenes de producción contiene.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_factura": {"type": "string", "description": "El número de la factura. Ej: FAC-001"}
                },
                "required": ["numero_factura"]
            }
        }
    }
]