import json

def ejecutar_crear_factura(env, parametros):
    try:
        nombre_cliente = parametros.get('nombre_cliente')
        codigos_ordenes = parametros.get('ordenes_produccion', [])
        
        # 1. Buscar al cliente
        cliente = env['cara.mia.cliente'].search([('nombre_cliente', 'ilike', nombre_cliente)], limit=1)
        if not cliente:
            return f"Error: No encontré al cliente '{nombre_cliente}' en la base de datos."
            
        if not codigos_ordenes:
            return "Error: Debes indicar al menos un código de orden de producción (o la palabra 'TODAS') para facturar."

        # Estandarizar la lista enviada por la IA
        if isinstance(codigos_ordenes, str):
            codigos_ordenes = [c.strip().upper() for c in codigos_ordenes.split(',') if c.strip()]
        else:
            codigos_ordenes = [str(c).strip().upper() for c in codigos_ordenes if str(c).strip()]

        ordenes_a_facturar = env['cara.mia.produccion']

        # 2. Lógica especial: "TODAS las finalizadas"
        if "TODAS" in codigos_ordenes:
            ordenes_a_facturar = env['cara.mia.produccion'].search([
                ('cliente_id', '=', cliente.id),
                ('state', '=', 'done')
            ])
            if not ordenes_a_facturar:
                return f"Aviso: El cliente {cliente.nombre_cliente} no tiene órdenes de producción finalizadas pendientes por facturar."
        else:
            # 3. Búsqueda y validación estricta orden por orden
            for codigo in codigos_ordenes:
                orden = env['cara.mia.produccion'].search([('name', '=', codigo)], limit=1)
                
                if not orden:
                    return f"Error: La orden de producción '{codigo}' no existe."
                
                # REGLA: Solo órdenes finalizadas
                if orden.state != 'done':
                    return f"Error: La orden '{codigo}' no se puede facturar porque no está finalizada (Estado actual: {orden.state})."
                
                # REGLA: La orden debe pertenecer al cliente facturado
                if orden.cliente_id.id != cliente.id:
                    return f"Error: La orden '{codigo}' pertenece al cliente {orden.cliente_id.nombre_cliente}, no puedes facturársela a {cliente.nombre_cliente}."
                
                ordenes_a_facturar |= orden  # Añadir al recordset

        # 4. Crear las líneas de la factura
        lineas_factura = []
        for orden in ordenes_a_facturar:
            precio_sugerido = orden.referencia_id.precio_venta_sugerido if orden.referencia_id else 0.0
            lineas_factura.append((0, 0, {
                'produccion_id': orden.id,
                'valor_unitario': precio_sugerido
            }))

        # 5. Crear el borrador de la factura
        nueva_factura = env['cara.mia.facturacion'].create({
            'cliente_id': cliente.id,
            'forma_pago': parametros.get('forma_pago', 'contado'),
            'fecha_vencimiento': parametros.get('fecha_vencimiento'),
            'linea_ids': lineas_factura
        })

        nombres_ordenes = ", ".join(ordenes_a_facturar.mapped('name'))
        return f"Éxito: Se creó el borrador de la factura {nueva_factura.name} para {cliente.nombre_cliente}. Incluye {len(ordenes_a_facturar)} orden(es) ({nombres_ordenes}) y tiene un total de ${nueva_factura.total_general}."

    except Exception as e:
        return f"Error al crear factura: {str(e)}"

def ejecutar_actualizar_factura(env, parametros):
    try:
        factura_str = parametros.get('numero_factura', '').strip().upper()
        fecha_vencimiento = parametros.get('fecha_vencimiento')
        ordenes_agregar = parametros.get('ordenes_agregar', [])
        ordenes_quitar = parametros.get('ordenes_quitar', [])

        factura = env['cara.mia.facturacion'].search([('name', '=', factura_str)], limit=1)
        if not factura:
            return f"Error: No se encontró la factura {factura_str}."

        # REGLA: Solo se modifican facturas en borrador
        if factura.estado != 'borrador':
            return f"Error: La factura {factura_str} está {factura.estado}. Solo puedes modificar facturas que estén en borrador."

        mensajes_resultado = []

        # 1. Actualizar fecha de vencimiento si la enviaron
        if fecha_vencimiento:
            factura.write({'fecha_vencimiento': fecha_vencimiento})
            mensajes_resultado.append(f"Fecha de vencimiento actualizada a {fecha_vencimiento}.")

        # Estandarizar arreglos
        if isinstance(ordenes_quitar, str):
            ordenes_quitar = [c.strip().upper() for c in ordenes_quitar.split(',') if c.strip()]
        if isinstance(ordenes_agregar, str):
            ordenes_agregar = [c.strip().upper() for c in ordenes_agregar.split(',') if c.strip()]

        # 2. Quitar órdenes
        for codigo_quitar in ordenes_quitar:
            linea = factura.linea_ids.filtered(lambda l: l.produccion_id.name == codigo_quitar)
            if linea:
                linea.unlink()
                mensajes_resultado.append(f"Orden {codigo_quitar} removida.")
            else:
                mensajes_resultado.append(f"La orden {codigo_quitar} no estaba en esta factura.")

        # 3. Agregar nuevas órdenes (con las mismas validaciones estrictas)
        for codigo_agregar in ordenes_agregar:
            if factura.linea_ids.filtered(lambda l: l.produccion_id.name == codigo_agregar):
                mensajes_resultado.append(f"La orden {codigo_agregar} ya estaba incluida.")
                continue

            orden = env['cara.mia.produccion'].search([('name', '=', codigo_agregar)], limit=1)
            if not orden:
                mensajes_resultado.append(f"Error: La orden {codigo_agregar} no existe.")
                continue

            if orden.state != 'done':
                mensajes_resultado.append(f"Error: La orden {codigo_agregar} no está finalizada.")
                continue

            if orden.cliente_id.id != factura.cliente_id.id:
                mensajes_resultado.append(f"Error: La orden {codigo_agregar} es de {orden.cliente_id.nombre_cliente}, no coincide con el cliente de la factura.")
                continue

            precio_sugerido = orden.referencia_id.precio_venta_sugerido if orden.referencia_id else 0.0
            factura.write({
                'linea_ids': [(0, 0, {
                    'produccion_id': orden.id,
                    'valor_unitario': precio_sugerido
                })]
            })
            mensajes_resultado.append(f"Orden {codigo_agregar} agregada exitosamente.")

        if not mensajes_resultado:
            return f"Aviso: No se solicitaron cambios o no se modificó nada en la factura {factura.name}."

        return f"Actualización de la factura {factura.name} completada. Resumen: " + " ".join(mensajes_resultado)

    except Exception as e:
        return f"Error al actualizar la factura: {str(e)}"

def ejecutar_emitir_factura(env, parametros):
    try:
        factura_str = parametros.get('numero_factura').strip().upper()
        factura = env['cara.mia.facturacion'].search([('name', '=', factura_str)], limit=1)
        
        if not factura:
            return f"Error: No se encontró la factura {factura_str}."
            
        if factura.estado != 'borrador':
            return f"Aviso: La factura {factura_str} ya se encuentra {factura.estado}."

        factura.action_emitir()
        
        return f"Éxito: La factura {factura.name} ha sido EMITIDA oficialmente. Se generó su cuenta de cobro automática con un saldo inicial de ${factura.saldo_pendiente}."
        
    except Exception as e:
        error_limpio = str(e).replace('\n', ' ')
        return f"Odoo impidió emitir la factura: {error_limpio}"

def ejecutar_consultar_factura(env, parametros):
    try:
        factura_str = parametros.get('numero_factura').strip().upper()
        factura = env['cara.mia.facturacion'].search([('name', '=', factura_str)], limit=1)
        
        if not factura:
            return f"Error: No se encontró la factura {factura_str}."

        ordenes_incluidas = []
        for linea in factura.linea_ids:
            ordenes_incluidas.append(f"{linea.produccion_id.name} ({linea.descripcion}) - Cantidad: {linea.cantidad}")

        info = {
            "cliente": factura.cliente_id.nombre_cliente,
            "estado": factura.estado,
            "forma_pago": factura.forma_pago,
            "fecha_facturacion": str(factura.fecha_facturacion),
            "fecha_vencimiento": str(factura.fecha_vencimiento),
            "total_general": factura.total_general,
            "saldo_pendiente": factura.saldo_pendiente,
            "ordenes_incluidas": ordenes_incluidas
        }
        
        return f"Detalles de la factura {factura.name}: {json.dumps(info)}"
        
    except Exception as e:
        return f"Error consultando factura: {str(e)}"