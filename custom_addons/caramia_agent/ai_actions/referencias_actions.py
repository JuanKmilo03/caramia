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
        ref = env['cara.mia.referencia'].search([('nombre_modelo', 'ilike', nombre)], limit=1)
        
        if not ref:
            return f"No se encontró ninguna referencia similar a '{nombre}'."

        info = {
            "codigo": ref.codigo_referencia,
            "nombre": ref.nombre_modelo,
            "estado": ref.estado,
            "precio_sugerido": ref.precio_venta_sugerido,
            "costo_materiales": ref.costo_total_insumos,
            "costo_mano_obra": ref.precio_total_labor,
            "costo_total_produccion": ref.costo_total_produccion
        }
        return f"Datos de la referencia: {json.dumps(info)}"
    except Exception as e:
        return f"Error en consulta: {str(e)}"


def ejecutar_editar_estado_referencia(env, parametros):
    try:
        nombre = parametros.get('nombre_modelo')
        ref = env['cara.mia.referencia'].search([('nombre_modelo', 'ilike', nombre)], limit=1)
        
        if not ref:
            return f"Error: No se encontró la referencia '{nombre}'."

        actualizaciones = {}
        if parametros.get('nuevo_estado'):
            actualizaciones['estado'] = parametros.get('nuevo_estado')
        if parametros.get('nuevo_precio') is not None:
            actualizaciones['precio_venta_sugerido'] = parametros.get('nuevo_precio')

        if not actualizaciones:
            return "No se proporcionaron datos para actualizar."

        ref.write(actualizaciones)
        return f"Éxito: Referencia '{ref.nombre_modelo}' actualizada correctamente."
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
            return f"ATENCION: Encontre la referencia '{nombre_guardado}'. Esta accion la borrara permanentemente. Pidele al usuario que confirme explicitamente si desea eliminarla. Si acepta, vuelve a llamar a esta herramienta con 'confirmado' en true."

        # En Odoo, unlink() falla automáticamente si hay restricciones de Foreign Key 
        # (ej: si tiene órdenes de producción gracias a tu ondelete='restrict')
        ref.unlink()
        return f"Éxito: La referencia '{nombre_guardado}' fue eliminada del sistema."
    except Exception as e:
        return f"No se puede eliminar la referencia (posiblemente esté en uso en órdenes de producción): {str(e)}"