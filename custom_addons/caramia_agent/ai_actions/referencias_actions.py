import json

def ejecutar_crear_referencia(env, parametros):
    try:
        nombre = parametros.get('nombre_modelo')
        
        # 1. Verificar si ya existe
        existe = env['cara.mia.referencia'].search([('nombre_modelo', 'ilike', nombre)], limit=1)
        if existe:
            return f"Error: Ya existe una referencia con el nombre '{existe.nombre_modelo}'."

        valores = {
            'nombre_modelo': nombre,
            'precio_venta_sugerido': parametros.get('precio_venta_sugerido', 0.0),
            'descripcion': parametros.get('descripcion', ''),
            'tipo_tarifa_header': 'manual'
        }

        # 2. Simular el 'default_get' para precargar las labores
        tipos_labor = env['cara.mia.tipo.labor'].search([])
        labor_lines = []
        for labor in tipos_labor:
            labor_lines.append((0, 0, {
                'tipo_labor_id': labor.id,
                'tarifa_pago': 0.0
            }))
        
        if labor_lines:
            valores['labor_ids'] = labor_lines

        # 3. Crear el registro
        nueva_ref = env['cara.mia.referencia'].create(valores)
        return f"Éxito: Se creó la referencia '{nueva_ref.nombre_modelo}' con código {nueva_ref.codigo_referencia}. Las labores de producción fueron precargadas en 0."
    except Exception as e:
        return f"Error al crear referencia: {str(e)}"


def ejecutar_consultar_referencia(env, parametros):
    try:
        nombre = parametros.get('nombre_modelo')
        
        # Si no se indica nombre, listar todas las referencias
        if not nombre:
            try:
                refs = env['cara.mia.referencia'].search([])
            except Exception as e:
                return f"Error al consultar referencias: {str(e)}"
            
            if not refs:
                return "No hay referencias registradas en el sistema."
            
            # Limitamos a un número razonable para evitar sobrecargas
            refs = refs[:100]
            
            lista = []
            for ref in refs:
                try:
                    # Obtener tarifas de labores de esta referencia
                    tarifas_labores = {}
                    for labor_line in ref.labor_ids:
                        if labor_line.tipo_labor_id:
                            tarifas_labores[labor_line.tipo_labor_id.name] = labor_line.tarifa_pago or 0.0
                    
                    lista.append({
                        "codigo": ref.codigo_referencia,
                        "nombre": ref.nombre_modelo,
                        "estado": ref.estado,
                        "precio_sugerido": ref.precio_venta_sugerido,
                        "tarifas_labores": tarifas_labores
                    })
                except Exception:
                    # Si hay algún campo que falla, continuamos con el siguiente
                    continue
            
            if not lista:
                return "No se pudieron obtener los datos de las referencias."
            
            return f"Referencias registradas ({len(lista)}):\n" + "\n".join([
                f"- {l['codigo']}: {l['nombre']} (${l['precio_sugerido']})\n    Labores: {l['tarifas_labores']}" 
                for l in lista
            ])
        
        # Si se indica nombre, buscar una referencia específica
        ref = env['cara.mia.referencia'].search([('nombre_modelo', 'ilike', nombre)], limit=1)
        
        if not ref:
            return f"No se encontró ninguna referencia similar a '{nombre}'."
        
        # Obtener tarifas de labores de esta referencia específica
        tarifas_labores = {}
        for labor_line in ref.labor_ids:
            if labor_line.tipo_labor_id:
                tarifas_labores[labor_line.tipo_labor_id.name] = labor_line.tarifa_pago or 0.0
        
        info = {
            "codigo": ref.codigo_referencia,
            "nombre": ref.nombre_modelo,
            "estado": ref.estado,
            "precio_sugerido": ref.precio_venta_sugerido,
            "tarifas_labores": tarifas_labores
        }
        return f"Datos de la referencia: {json.dumps(info)}"
    except Exception as e:
        return f"Error en consulta: {str(e)}"

def ejecutar_editar_referencia(env, parametros):
    try:
        nombre = parametros.get('nombre_modelo')
        ref = env['cara.mia.referencia'].search([('nombre_modelo', 'ilike', nombre)], limit=1)
        
        if not ref:
            return f"Error: No se encontró la referencia '{nombre}'."

        actualizaciones = {}
        detalles = []
        
        # 1. Cambiar el tipo de tarifa y actualizar labores automáticamente
        tipo_tarifa = parametros.get('tipo_tarifa_header')
        if tipo_tarifa in ['manual', '1', '2']:
            actualizaciones['tipo_tarifa_header'] = tipo_tarifa
            nombre_tarifa = 'Sugerido 1' if tipo_tarifa == '1' else 'Sugerido 2' if tipo_tarifa == '2' else 'Manual'
            detalles.append(f"Origen de precios de labor: {nombre_tarifa}")
            
            # Como el @api.onchange no se dispara desde el backend, replicamos la lógica aquí
            if tipo_tarifa != 'manual':
                for linea in ref.labor_ids:
                    if linea.tipo_labor_id:
                        if tipo_tarifa == '1':
                            linea.tarifa_pago = linea.tipo_labor_id.tarifa_normal or 0.0
                        elif tipo_tarifa == '2':
                            linea.tarifa_pago = linea.tipo_labor_id.tarifa_especial or 0.0
        
        # 2. Actualizar precio de venta sugerido
        if parametros.get('precio_venta_sugerido') is not None:
            actualizaciones['precio_venta_sugerido'] = parametros.get('precio_venta_sugerido')
            detalles.append(f"Precio venta público: {actualizaciones['precio_venta_sugerido']}")
            
        # 3. Actualizar tarifas manuales individuales (si aplica)
        tarifas_manuales = parametros.get('nuevas_tarifas_labores')
        if tarifas_manuales and isinstance(tarifas_manuales, dict):
            # Si mandan tarifas manuales, forzamos el header a manual para evitar inconsistencias
            actualizaciones['tipo_tarifa_header'] = 'manual'
            for key, valor in tarifas_manuales.items():
                for line in ref.labor_ids:
                    if line.tipo_labor_id and line.tipo_labor_id.name == key:
                        line.tarifa_pago = valor
                        break
            detalles.append(f"Tarifas manuales ajustadas: {tarifas_manuales}")

        if not actualizaciones and not detalles:
            return "No se proporcionaron datos válidos para actualizar."
            
        # Guardar los cambios principales en el encabezado
        if actualizaciones:
            ref.write(actualizaciones)
            
        # Construir el mensaje de éxito para que la IA se lo lea al usuario
        mensaje = f"Éxito: Referencia '{ref.nombre_modelo}' actualizada correctamente. "
        mensaje += " - ".join(detalles)
        
        return mensaje
        
    except Exception as e:
        return f"Error al editar: {str(e)}"

def ejecutar_eliminar_referencia(env, parametros):
    try:
        nombre = parametros.get('nombre_modelo')
        ref = env['cara.mia.referencia'].search([('nombre_modelo', 'ilike', nombre)], limit=1)
        
        if not ref:
            return f"Error: No se encontró la referencia '{nombre}'."
        
        nombre_guardado = ref.nombre_modelo
        
        confirmado = parametros.get('confirmado', False)
        if not confirmado:
            return f"ATENCION: Encontre la referencia '{nombre_guardado}'. Esta accion la borrara permanentemente. Pidele al usuario que confirme explícitamente si desea eliminarla. Si acepta, vuelve a llamar a esta herramienta con 'confirmado' en true."
        
        # En Odoo, unlink() falla automáticamente si hay restricciones de Foreign Key 
        # (ej: si tiene órdenes de producción gracias a tu ondelete='restrict')
        ref.unlink()
        return f"Éxito: La referencia '{nombre_guardado}' fue eliminada del sistema."
    except Exception as e:
        return f"No se puede eliminar la referencia (posiblemente esté en uso en órdenes de producción): {str(e)}"