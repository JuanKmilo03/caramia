# Módulo: tools/clientes_tools.py

# Aquí guardamos ÚNICAMENTE las definiciones (El "Menú") que la IA necesita leer 
# para entender qué puede hacer con los clientes.

HERRAMIENTAS_CLIENTES = [
    {
        "type": "function",
        "function": {
            "name": "crear_cliente",
            "description": "Crea un nuevo cliente en la base de datos de Odoo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {"type": "string", "description": "Nombre del cliente"},
                    "telefono_cliente": {"type": "string", "description": "Teléfono del cliente"},
                    "direccion": {"type": "string", "description": "Dirección del cliente"},
                    "sello": {"type": "string", "description": "Sello o marca"}
                },
                "required": ["nombre_cliente"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_clientes",
            "description": "Consulta la lista de clientes registrados en Odoo.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_cliente",
            "description": "Actualiza los datos (teléfono, dirección o sello) de un cliente existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_actual": {"type": "string", "description": "El nombre actual del cliente a modificar"},
                    "nuevo_telefono": {"type": "string", "description": "Nuevo número de teléfono (opcional)"},
                    "nueva_direccion": {"type": "string", "description": "Nueva dirección (opcional)"},
                    "nuevo_sello": {"type": "string", "description": "Nuevo sello (opcional)"}
                },
                "required": ["nombre_actual"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "eliminar_cliente",
            "description": "Elimina un cliente de la base de datos de Odoo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {"type": "string", "description": "Nombre exacto del cliente a eliminar"}
                },
                "required": ["nombre_cliente"]
            }
        }
    }
]