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
    }
]