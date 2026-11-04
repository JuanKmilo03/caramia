import json

def ejecutar_crear_orden(env, parametros):
    try:
        nombre_cliente = parametros.get('nombre_cliente')
        nombre_ref = parametros.get('nombre_referencia')
        tallas = parametros.get('tallas', {})

        # 1. Buscar Cliente
        cliente = env['cara.mia.cliente'].search([('nombre_cliente', 'ilike', nombre_cliente)], limit=1)
        if not cliente:
            return f"Error: No encontré al cliente '{nombre_cliente}' en la base de datos."

        # 2. Buscar Referencia
        referencia = env['cara.mia.referencia'].search([
            ('nombre_modelo', 'ilike', nombre_ref), 
            ('estado', '=', 'activo')
        ], limit=1)
        if not referencia:
            return f"Error: No encontré la referencia '{nombre_ref}' o está inactiva."

        sello_bd = getattr(cliente, 'sello', None)
        sello_final = sello_bd if sello_bd else parametros.get('sello', 'Sin Sello')

        # 3. Preparar el diccionario base
        valores_produccion = {
            'cliente_id': cliente.id,
            'referencia_id': referencia.id,
            'color': parametros.get('color', ''),
            'material': parametros.get('material', ''),
            'sello': sello_final
        }

        # 4. Asignar las tallas dinámicamente
        for talla, cantidad in tallas.items():
            campo_talla = f"talla_{talla}"
            # Validamos que el campo exista (ej: talla_21 hasta talla_40)
            if campo_talla in env['cara.mia.produccion']._fields:
                valores_produccion[campo_talla] = int(cantidad)

        # 5. Copiar las labores de la referencia
        labores_list = []
        for labor_ref in referencia.labor_ids:
            if labor_ref.tipo_labor_id:
                labores_list.append((0, 0, {
                    'tipo_labor_id': labor_ref.tipo_labor_id.id,
                    'tarifa_pago': labor_ref.tarifa_pago or 0.0
                }))
        
        if labores_list:
            valores_produccion['labor_ids'] = labores_list

        # 6. Crear la orden
        nueva_orden = env['cara.mia.produccion'].create(valores_produccion)
        return f"Éxito: Orden de producción '{nueva_orden.name}' creada para el cliente {cliente.nombre_cliente}. Total de pares: {nueva_orden.total_pares}."
    
    except Exception as e:
        return f"Error al crear la orden de producción: {str(e)}"

def ejecutar_consultar_ordenes(env, parametros):
    try:
        ordenes = env['cara.mia.produccion'].search_read(
            [], 
            ['name', 'cliente_id', 'referencia_id', 'state', 'total_pares', 'date'],
            limit=20
        )
        if not ordenes:
            return "No hay órdenes de producción registradas."

        # Limpiar datos para la IA
        for ord in ordenes:
            ord['cliente'] = ord['cliente_id'][1] if ord.get('cliente_id') else 'N/A'
            ord['referencia'] = ord['referencia_id'][1] if ord.get('referencia_id') else 'N/A'
            del ord['cliente_id']
            del ord['referencia_id']

        return f"Lista de órdenes: {json.dumps(ordenes, default=str)}"
    except Exception as e:
        return f"Error consultando órdenes: {str(e)}"

def ejecutar_cambiar_estado_orden(env, parametros):
    try:
        numero = parametros.get('numero_orden')
        estado_solicitado = parametros.get('nuevo_estado')
        
        # 1. Bloqueo de seguridad: El bot no puede finalizar órdenes
        if estado_solicitado == 'done':
            return "Error de seguridad: No tengo permisos para marcar una orden como 'Finalizada'. Esto debe hacerse mediante el proceso regular del sistema."

        orden = env['cara.mia.produccion'].search([('name', '=', numero)], limit=1)
        
        if not orden:
            return f"Error: No se encontró la orden {numero}."
            
        # 2. BLOQUEO ESTRICTO: Estados definitivos (Cancelado o Finalizado)
        if orden.state in ['canceled', 'done']:
            nombre_estado_actual = 'CANCELADA' if orden.state == 'canceled' else 'FINALIZADA'
            return f"Error: La orden {numero} ya se encuentra {nombre_estado_actual}. Este es un estado final y no se permite cambiarla a '{estado_solicitado}'."

        # 3. Validar si ya está en ese estado
        if orden.state == estado_solicitado:
            return f"Atención: La orden {numero} ya se encuentra en ese estado."

        # 4. Ejecutar el cambio
        if estado_solicitado == 'in_progress' and hasattr(orden, 'action_set_in_progress'):
            orden.action_set_in_progress()
        elif estado_solicitado == 'canceled' and hasattr(orden, 'action_cancel'):
            orden.action_cancel()
        else:
            # Para draft, stopped, o si no existen los actions anteriores
            orden.write({'state': estado_solicitado})

        # Mapeo de nombres para que la IA responda de forma natural
        nombres_bonitos = {
            'draft': 'Borrador',
            'in_progress': 'En Proceso',
            'stopped': 'Detenido',
            'canceled': 'Cancelado'
        }
        estado_final_str = nombres_bonitos.get(estado_solicitado, estado_solicitado)

        return f"Éxito: La orden {numero} ha sido movida correctamente al estado '{estado_final_str}'."

    except Exception as e:
        return f"Error cambiando el estado de la orden: {str(e)}"