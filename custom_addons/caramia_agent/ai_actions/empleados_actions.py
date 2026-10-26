import json

import json

def ejecutar_crear_empleado(env, parametros):
    try:
        nombre_labor = parametros.get('nombre_labor')
        LaborModel = env['cara.mia.tipo.labor']
        
        labor_buscada_norm = LaborModel._normalizar_texto(nombre_labor)
        todas_las_labores = LaborModel.search([])
        
        labor_encontrada = None
        nombres_disponibles = [] # Guardaremos las labores que sí existen
        
        for labor in todas_las_labores:
            nombres_disponibles.append(labor.name) # Alimentamos la lista
            if LaborModel._normalizar_texto(labor.name) == labor_buscada_norm:
                labor_encontrada = labor
                break
                
        # Búsqueda de respaldo clásica de Odoo por si acaso
        if not labor_encontrada:
            labor_encontrada = LaborModel.search([('name', 'ilike', nombre_labor)], limit=1)
        
        # ¡LA MAGIA OCURRE AQUÍ!
        if not labor_encontrada:
            lista_nombres = ", ".join(nombres_disponibles)
            return f"Error: No se encontró la labor '{nombre_labor}'. Las labores disponibles son: {lista_nombres}. Dile al usuario cuáles están disponibles para que elija una."

        nuevo_empleado = env['cara.mia.empleado'].create({
            'empleado_id': parametros.get('cedula'),
            'nombre_empleado': parametros.get('nombre_empleado'),
            'telefono_empleado': parametros.get('telefono_empleado'),
            'tipo_labor_id': labor_encontrada.id
        })
        return f"Éxito: Empleado '{nuevo_empleado.nombre_empleado}' creado con la labor '{labor_encontrada.name}'."
    except Exception as e:
        return f"Error al crear empleado en BD: {str(e)}"

def ejecutar_consultar_empleados(env, parametros):
    try:
        empleados = env['cara.mia.empleado'].search_read(
            [], 
            ['empleado_id', 'nombre_empleado', 'telefono_empleado', 'tipo_labor_id', 'total_prestamos_pendientes']
        )
        if empleados:
            # Limpiamos el Many2one para que la IA lo entienda fácil
            for emp in empleados:
                if emp.get('tipo_labor_id'):
                    emp['labor'] = emp['tipo_labor_id'][1] # Tomamos solo el nombre
                    del emp['tipo_labor_id']
            return f"Datos crudos de Odoo: {json.dumps(empleados)}"
        else:
            return "No hay empleados registrados."
    except Exception as e:
        return f"Error buscando empleados: {str(e)}"

def ejecutar_eliminar_empleado(env, parametros):
    try:
        cedula = parametros.get('cedula')
        empleado = env['cara.mia.empleado'].search([('empleado_id', '=', cedula)], limit=1)
        
        if not empleado:
            return f"Error: No se encontró ningún empleado con la cédula '{cedula}'."
            
        nombre = empleado.nombre_empleado
        empleado.unlink()
        return f"Éxito: El empleado '{nombre}' ha sido eliminado."
    except Exception as e:
        return f"Error eliminando empleado (¿Tiene historial de trabajo o préstamos?): {str(e)}"

def ejecutar_registrar_prestamo(env, parametros):
    try:
        cedula = parametros.get('cedula_empleado')
        empleado = env['cara.mia.empleado'].search([('empleado_id', '=', cedula)], limit=1)
        
        if not empleado:
            return f"Error: No se encontró empleado con cédula '{cedula}'."

        nuevo_prestamo = env['cara.mia.prestamo'].create({
            'empleado_id': empleado.id,
            'monto': parametros.get('monto'),
            'observaciones': parametros.get('observacion', 'Préstamo gestionado por IA')
        })
        return f"Éxito: Préstamo de {nuevo_prestamo.monto} registrado para {empleado.nombre_empleado}. Su nuevo saldo pendiente es {empleado.total_prestamos_pendientes}."
    except Exception as e:
        return f"Error registrando préstamo: {str(e)}"