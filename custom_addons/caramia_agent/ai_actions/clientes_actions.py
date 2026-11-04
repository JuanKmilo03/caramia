import json

def ejecutar_crear_cliente(env, parametros):
    try:
        nuevo_cliente = env['cara.mia.cliente'].create(parametros)
        return f"Éxito: Cliente creado con ID {nuevo_cliente.id}"
    except Exception as e:
        return f"Error en BD Odoo: {str(e)}"

def ejecutar_consultar_clientes(env, parametros):
    try:
        clientes = env['cara.mia.cliente'].search_read(
            [], 
            ['id', 'nombre_cliente', 'telefono_cliente', 'direccion', 'sello'],
        )
        
        if clientes:
            return f"Datos crudos de Odoo: {json.dumps(clientes)}"
        else:
            return "No hay clientes registrados."
    except Exception as e:
        return f"Error buscando en Odoo: {str(e)}"

def ejecutar_actualizar_cliente(env, parametros):
    try:
        nombre_actual = parametros.get('nombre_actual')
        cliente = env['cara.mia.cliente'].search([('nombre_cliente', 'ilike', nombre_actual)], limit=1)
        
        if not cliente:
            return f"Error: No se encontró ningún cliente llamado '{nombre_actual}'."

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
        confirmado = parametros.get('confirmado', False)

        cliente = env['cara.mia.cliente'].search([('nombre_cliente', 'ilike', nombre)], limit=1)
        
        if not cliente:
            return f"Error: No se encontró ningún cliente llamado '{nombre}' para eliminar."
            
        # MAGIA DE CONFIRMACIÓN PARA LA IA
        if not confirmado:
            return f"⚠️ ATENCIÓN: Encontré al cliente '{cliente.nombre_cliente}'. Esta acción lo borrará permanentemente de la base de datos. Pídele al usuario que confirme explícitamente si desea eliminarlo. Si el usuario acepta, vuelve a llamar a esta herramienta con 'confirmado' en true."
            
        nombre_eliminado = cliente.nombre_cliente
        cliente.unlink() 
        return f"Éxito: El cliente '{nombre_eliminado}' ha sido eliminado de la base de datos."
        
    except Exception as e:
        return f"Error eliminando en Odoo (¿Tiene facturas, órdenes o movimientos asociados?): {str(e)}"