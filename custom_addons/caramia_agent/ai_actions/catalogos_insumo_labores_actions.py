import json

def ejecutar_crear_tipo_labor(env, parametros):
    try:
        valores = {
            'name': parametros.get('nombre'),
            'tarifa_normal': parametros.get('tarifa_normal', 0.0),
            'tarifa_especial': parametros.get('tarifa_especial', 0.0)
        }
        # Odoo lanzará el ValidationError automáticamente si tu función _normalizar_texto detecta duplicados
        nueva_labor = env['cara.mia.tipo.labor'].create(valores)
        return f"Éxito: Labor '{nueva_labor.name}' creada. Tarifa Normal: {nueva_labor.tarifa_normal}, Especial: {nueva_labor.tarifa_especial}."
    except Exception as e:
        return f"Error al crear labor: {str(e)}"

def ejecutar_consultar_labores(env, parametros):
    try:
        labores = env['cara.mia.tipo.labor'].search_read([], ['name', 'tarifa_normal', 'tarifa_especial'])
        if not labores:
            return "No hay labores registradas en el sistema."
        return f"Labores disponibles: {json.dumps(labores)}"
    except Exception as e:
        return f"Error consultando labores: {str(e)}"

def ejecutar_actualizar_labor(env, parametros):
    try:
        nombre_actual = parametros.get('nombre_actual')
        labor = env['cara.mia.tipo.labor'].search([('name', 'ilike', nombre_actual)], limit=1)
        
        if not labor:
            return f"Error: No se encontró la labor '{nombre_actual}' en el sistema."

        valores = {}
        if parametros.get('nuevo_nombre'):
            valores['name'] = parametros.get('nuevo_nombre')
        if parametros.get('tarifa_normal') is not None:
            valores['tarifa_normal'] = parametros.get('tarifa_normal')
        if parametros.get('tarifa_especial') is not None:
            valores['tarifa_especial'] = parametros.get('tarifa_especial')

        if not valores:
            return "Aviso: No se enviaron datos nuevos para actualizar la labor."

        labor.write(valores)
        return f"Éxito: Labor actualizada. Nombre: {labor.name}, Tarifa Normal: {labor.tarifa_normal}, Especial: {labor.tarifa_especial}."
    except Exception as e:
        return f"Error al actualizar la labor: {str(e)}"

def ejecutar_borrar_labor(env, parametros):
    try:
        nombre = parametros.get('nombre')
        confirmado = parametros.get('confirmado', False)

        labor = env['cara.mia.tipo.labor'].search([('name', 'ilike', nombre)], limit=1)
        
        if not labor:
            return f"Error: No se encontró la labor '{nombre}'."

        # MAGIA DE CONFIRMACIÓN PARA LA IA
        if not confirmado:
            return f"⚠️ ATENCIÓN: Encontré la labor '{labor.name}'. Esta acción la borrará permanentemente. Pídele al usuario que confirme explícitamente si está seguro de eliminarla. Si el usuario acepta, vuelve a ejecutar esta herramienta pasando el parámetro 'confirmado' como true."

        nombre_labor = labor.name
        labor.unlink()
        return f"Éxito: La labor '{nombre_labor}' ha sido eliminada del sistema."
    except Exception as e:
        return f"Error al borrar la labor: {str(e)}"



    

def ejecutar_crear_insumo(env, parametros):
    try:
        tipo_nombre = parametros.get('tipo_componente')
        
        # MAGIA: Buscar o crear el tipo de componente al vuelo si no existe
        tipo = env['cara.mia.tipo.componente'].search([('name', 'ilike', tipo_nombre)], limit=1)
        if not tipo:
            tipo = env['cara.mia.tipo.componente'].create({'name': tipo_nombre.capitalize()})
        
        valores = {
            'name': parametros.get('nombre'),
            'tipo_componente_id': tipo.id,
            'unidad_medida': parametros.get('unidad_medida'),
            'costo_referencia': parametros.get('costo_referencia', 0.0),
            'stock_minimo': parametros.get('stock_minimo', 0.0)
        }
        
        nuevo_insumo = env['cara.mia.insumo.catalogo'].create(valores)
        return f"Éxito: Insumo '{nuevo_insumo.name}' creado exitosamente bajo la categoría '{tipo.name}'."
    except Exception as e:
        return f"Error al crear insumo: {str(e)}"

def ejecutar_consultar_insumos(env, parametros):
    try:
        nombre = parametros.get('nombre', '')
        dominio = [('name', 'ilike', nombre)] if nombre else []
        insumos = env['cara.mia.insumo.catalogo'].search(dominio, limit=20)
        
        if not insumos:
            return f"No se encontraron insumos que coincidan con '{nombre}'."
        
        lista = []
        for ins in insumos:
            lista.append({
                "nombre": ins.name,
                "categoria": ins.tipo_componente_id.name if ins.tipo_componente_id else '',
                "unidad": ins.unidad_medida,
                "costo_referencia": ins.costo_referencia,
                "stock_actual": ins.stock_actual
            })
        return f"Insumos encontrados: {json.dumps(lista)}"
    except Exception as e:
        return f"Error consultando insumos: {str(e)}"

def ejecutar_actualizar_insumo(env, parametros):
    try:
        nombre_actual = parametros.get('nombre_actual')
        insumo = env['cara.mia.insumo.catalogo'].search([('name', 'ilike', nombre_actual)], limit=1)
        
        if not insumo:
            return f"Error: No se encontró el insumo '{nombre_actual}'."

        valores = {}
        if parametros.get('nuevo_nombre'):
            valores['name'] = parametros.get('nuevo_nombre')
        if parametros.get('unidad_medida'):
            valores['unidad_medida'] = parametros.get('unidad_medida')
        if parametros.get('costo_referencia') is not None:
            valores['costo_referencia'] = parametros.get('costo_referencia')
        if parametros.get('stock_minimo') is not None:
            valores['stock_minimo'] = parametros.get('stock_minimo')

        if parametros.get('tipo_componente'):
            tipo_nombre = parametros.get('tipo_componente')
            tipo = env['cara.mia.tipo.componente'].search([('name', 'ilike', tipo_nombre)], limit=1)
            if not tipo:
                tipo = env['cara.mia.tipo.componente'].create({'name': tipo_nombre.capitalize()})
            valores['tipo_componente_id'] = tipo.id

        if not valores:
            return "Aviso: No se enviaron datos nuevos para actualizar el insumo."

        insumo.write(valores)
        return f"Éxito: Insumo '{insumo.name}' actualizado correctamente."
    except Exception as e:
        return f"Error al actualizar el insumo: {str(e)}"

def ejecutar_borrar_insumo(env, parametros):
    try:
        nombre = parametros.get('nombre')
        confirmado = parametros.get('confirmado', False)

        insumo = env['cara.mia.insumo.catalogo'].search([('name', 'ilike', nombre)], limit=1)
        
        if not insumo:
            return f"Error: No se encontró el insumo '{nombre}'."

        # MAGIA DE CONFIRMACIÓN PARA LA IA
        if not confirmado:
            return f"⚠️ ATENCIÓN: Encontré el insumo '{insumo.name}'. Esta acción lo borrará permanentemente. Pídele al usuario que confirme explícitamente si desea eliminarlo. Si el usuario acepta, vuelve a llamar a esta herramienta con 'confirmado' en true."

        nombre_insumo = insumo.name
        insumo.unlink()
        return f"Éxito: El insumo '{nombre_insumo}' ha sido eliminado definitivamente."
    except Exception as e:
        return f"Error al borrar el insumo: {str(e)}"