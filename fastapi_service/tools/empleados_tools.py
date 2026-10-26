
HERRAMIENTAS_EMPLEADOS = [
    {
        "type": "function",
        "function": {
            "name": "crear_empleado",
            "description": "Crea un nuevo empleado en Odoo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula": {"type": "string", "description": "Número de documento o cédula"},
                    "nombre_empleado": {"type": "string", "description": "Nombre completo del empleado"},
                    "telefono_empleado": {"type": "string", "description": "Teléfono del empleado"},
                    "nombre_labor": {"type": "string", "description": "El nombre del tipo de labor que realiza (ej: Corte, Costura, etc.)"}
                },
                "required": ["cedula", "nombre_empleado", "telefono_empleado", "nombre_labor"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_empleados",
            "description": "Consulta la lista de empleados y sus saldos pendientes por préstamos.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "eliminar_empleado",
            "description": "Elimina un empleado usando su número de cédula.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula": {"type": "string", "description": "Cédula del empleado a eliminar"}
                },
                "required": ["cedula"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_prestamo",
            "description": "Registra un nuevo préstamo o descuento a un empleado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula_empleado": {"type": "string", "description": "Cédula del empleado que recibe el préstamo"},
                    "monto": {"type": "number", "description": "Valor monetario del préstamo"},
                    "observacion": {"type": "string", "description": "Motivo del préstamo"}
                },
                "required": ["cedula_empleado", "monto"]
            }
        }
    }
]