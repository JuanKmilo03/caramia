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


def ejecutar_actualizar_cliente(env, parametros):
    try:
        nombre_actual = parametros.get('nombre_actual')
        # Buscamos al cliente (ilike permite buscar ignorando mayúsculas/minúsculas)
        cliente = env['cara.mia.cliente'].search([('nombre_cliente', 'ilike', nombre_actual)], limit=1)
        
        if not cliente:
            return f"Error: No se encontró ningún cliente llamado '{nombre_actual}'."

        # Preparamos solo los datos que la IA decidió enviar
        valores = {}
        if 'nuevo_telefono' in parametros:
            valores['telefono_cliente'] = parametros['nuevo_telefono']
        if 'nueva_direccion' in parametros:
            valores['direccion'] = parametros['nueva_direccion']
        if 'nuevo_sello' in parametros:
            valores['sello'] = parametros['nuevo_sello']
            
        if valores:
            cliente.write(valores)
            return f"Éxito: Cliente '{cliente.nombre_cliente}' actualizado con los nuevos datos."
        else:
            return "No se recibieron datos nuevos para actualizar."
            
    except Exception as e:
        return f"Error actualizando en Odoo: {str(e)}"

def ejecutar_eliminar_cliente(env, parametros):
    try:
        nombre = parametros.get('nombre_cliente')
        cliente = env['cara.mia.cliente'].search([('nombre_cliente', 'ilike', nombre)], limit=1)
        
        if not cliente:
            return f"Error: No se encontró ningún cliente llamado '{nombre}' para eliminar."
            
        nombre_eliminado = cliente.nombre_cliente
        cliente.unlink() # Comando de Odoo para borrar el registro
        return f"Éxito: El cliente '{nombre_eliminado}' ha sido eliminado de la base de datos."
        
    except Exception as e:
        return f"Error eliminando en Odoo (¿Tiene facturas asociadas?): {str(e)}"