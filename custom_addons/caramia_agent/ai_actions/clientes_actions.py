import json

def ejecutar_crear_cliente(env, parametros):
    try:
        nuevo_cliente = env['cara.mia.cliente'].create(parametros)
        return f"Éxito: Cliente creado con ID {nuevo_cliente.id}"
    except Exception as e:
        return f"Error en BD Odoo: {str(e)}"

def ejecutar_consultar_clientes(env, parametros):
    try:
        # Traemos toda la info útil disponible (limitamos a 10 para no saturar)
        clientes = env['cara.mia.cliente'].search_read(
            [], 
            ['id', 'nombre_cliente', 'telefono_cliente', 'direccion', 'sello'],
        )
        
        if clientes:
            # Le pasamos a la IA los datos puros en formato JSON para que ella los analice
            return f"Datos crudos de Odoo: {json.dumps(clientes)}"
        else:
            return "No hay clientes registrados."
    except Exception as e:
        return f"Error buscando en Odoo: {str(e)}"