import json
import unicodedata
import difflib

def limpiar_texto(texto):
    if not texto: return ''
    # Separa las letras de sus tildes y las elimina para una comparación limpia
    texto_norm = unicodedata.normalize('NFD', str(texto))
    return texto_norm.encode('ascii', 'ignore').decode('utf-8').lower().strip()

def ejecutar_registrar_tiquete(env, parametros):
    try:
        nombre = parametros.get('nombre_empleado', '')
        codigos = parametros.get('codigo_orden', [])
        
        # 1. Procesar los códigos
        if isinstance(codigos, str):
            codigos = [c.strip().upper() for c in codigos.split(',') if c.strip()]
        else:
            codigos = [str(c).strip().upper() for c in codigos if str(c).strip()]

        if not codigos:
            return "Error: Debes proporcionar al menos un código de orden de producción."

        # 2. Búsqueda segura (SIN sudo)
        todos_los_empleados = env['cara.mia.empleado'].search([])
        nombre_buscado = limpiar_texto(nombre)
        empleados_coincidentes = []
        nombres_en_bd = []
        
        # 3. Emparejamiento ultra-flexible
        for emp in todos_los_empleados:
            nom_bd = emp.nombre_empleado
            if not nom_bd: continue
            
            nombres_en_bd.append(str(nom_bd))
            nom_norm = limpiar_texto(nom_bd)
            
            if nombre_buscado in nom_norm or nom_norm in nombre_buscado:
                if emp not in empleados_coincidentes:
                    empleados_coincidentes.append(emp)
            else:
                palabras_buscadas = nombre_buscado.split()
                palabras_bd = nom_norm.split()
                if all(p in palabras_bd for p in palabras_buscadas):
                     if emp not in empleados_coincidentes:
                         empleados_coincidentes.append(emp)

        # 4. Similitud (Fuzzy Match)
        if not empleados_coincidentes:
            sugerencias = []
            palabras_buscadas = nombre_buscado.split()
            
            for emp in todos_los_empleados:
                if not emp.nombre_empleado: continue
                nom_norm = limpiar_texto(emp.nombre_empleado)
                palabras_emp = nom_norm.split()
                
                for p_buscada in palabras_buscadas:
                    if difflib.get_close_matches(p_buscada, palabras_emp, n=1, cutoff=0.75):
                        if emp not in sugerencias:
                            sugerencias.append(emp)
                        break
            
            if sugerencias:
                nombres_sugeridos = " o ".join([e.nombre_empleado for e in sugerencias])
                return f"Error: No encontré a '{nombre}'. ¿Te referías a: {nombres_sugeridos}?"
            else:
                return f"Error: No logré emparejar '{nombre}'. Dile al usuario que revise el nombre. (En la BD veo: {nombres_en_bd})"

        if len(empleados_coincidentes) > 1:
            nombres_opciones = " y ".join([e.nombre_empleado for e in empleados_coincidentes])
            return f"Atención: Encontré varias personas para '{nombre}': {nombres_opciones}. Pregunta a cuál de ellas se refiere."

        empleado = empleados_coincidentes[0]
        exitos = []
        errores = []
        
        for codigo in codigos:
            try:
                # A. Buscar si la orden de producción existe
                orden = env['cara.mia.produccion'].search([('name', '=', codigo)], limit=1)
                if not orden:
                    errores.append(f"{codigo} (No existe en el sistema)")
                    continue
                
                # B. Validar estado de la orden ('in_progress')
                if orden.state != 'in_progress':
                    errores.append(f"{codigo} (Rechazada: La orden no está 'En Proceso' actualmente)")
                    continue
                
                # C. Validar tiquetes previos por LABOR/TRABAJO
                # Quitamos el limit=1 para traer TODOS los tickets de esta orden
                tiquetes_previos = env['cara.mia.registro.trabajo.orden'].search([('orden_codigo', '=', codigo)])
                trabajo_bloqueado = False
                
                for tiquete in tiquetes_previos:
                    # Regla 1: El mismo empleado no puede registrarse dos veces en la misma orden
                    if tiquete.empleado_id.id == empleado.id:
                        errores.append(f"{codigo} (Rechazada: {empleado.nombre_empleado} ya tiene registrado su ticket en esta orden)")
                        trabajo_bloqueado = True
                        break
                    
                    # Regla 2: Otro empleado ya hizo ESA MISMA LABOR
                    # IMPORTANTE: Revisa que el campo se llame 'labor_id' en tu modelo cara.mia.empleado
                    if tiquete.empleado_id.tipo_labor_id and empleado.tipo_labor_id:
                        if tiquete.empleado_id.tipo_labor_id.id == empleado.tipo_labor_id.id:
                            errores.append(f"{codigo} (Rechazada: La labor '{empleado.tipo_labor_id.name}' ya fue realizada en esta orden por {tiquete.empleado_id.nombre_empleado})")
                            trabajo_bloqueado = True
                            break
                
                # Si rompió alguna de las reglas, saltamos a la siguiente orden
                if trabajo_bloqueado:
                    continue

                # D. Si pasa todas las validaciones, creamos el registro
                env['cara.mia.registro.trabajo.orden'].create({
                    'empleado_id': empleado.id,
                    'orden_codigo': codigo
                })
                exitos.append(codigo)
                
            except Exception as e:
                errores.append(f"{codigo} (Error de sistema: {str(e)})")

        # 6. Respuesta final
        mensaje = f"Resultados para {empleado.nombre_empleado}:\n"
        if exitos: mensaje += f"- Asignados con éxito: {', '.join(exitos)}\n"
        if errores: mensaje += f"- Problemas encontrados: {'; '.join(errores)}\n"
        return mensaje

    except Exception as e:
        return f"Error interno procesando tiquetes: {str(e)}"
    
def ejecutar_generar_nomina(env, parametros):
    try:
        f_inicio = parametros.get('fecha_inicio')
        f_fin = parametros.get('fecha_fin')
        
        # 1. Crear el registro "Padre" de la nómina
        nueva_nomina = env['cara.mia.pago.empleado'].create({
            'fecha_inicio': f_inicio,
            'fecha_fin': f_fin
        })
        
        # 2. Llamar a tu función de cálculo automático
        nueva_nomina.action_calcular_pagos()
        
        if nueva_nomina.cantidad_lineas == 0:
            # Si no encontró tiquetes, borramos el documento huérfano
            nueva_nomina.unlink()
            return f"No se generó la nómina porque no hay tiquetes pendientes entre {f_inicio} y {f_fin}."
            
        return f"Éxito: Nómina generada en estado En Proceso. Se incluyeron {nueva_nomina.cantidad_lineas} empleados con un total a pagar de ${nueva_nomina.total_neto}. Dile al usuario que debe ir al sistema a marcar los pagos como 'pagado = True' para poder finalizarla."
    except Exception as e:
        return f"Error al generar nómina: {str(e)}"

def ejecutar_actualizar_nomina(env, parametros):
    try:
        ref = parametros.get('referencia_nomina', '').strip()
        nomina = env['cara.mia.pago.empleado'].search([('name', 'ilike', ref)], limit=1)
        
        if not nomina:
            return f"Error: No encontré la nómina '{ref}'."

        valores = {}
        if parametros.get('nueva_fecha_inicio'):
            valores['fecha_inicio'] = parametros.get('nueva_fecha_inicio')
        if parametros.get('nueva_fecha_fin'):
            valores['fecha_fin'] = parametros.get('nueva_fecha_fin')

        if not valores:
            return "Aviso: No se enviaron datos nuevos para actualizar la nómina."

        nomina.write(valores)
        return f"Éxito: Nómina '{nomina.name}' actualizada correctamente."
    except Exception as e:
        return f"Error al actualizar la nómina: {str(e)}"

def ejecutar_borrar_nomina(env, parametros):
    try:
        ref = parametros.get('referencia_nomina', '').strip()
        confirmado = parametros.get('confirmado', False)

        nomina = env['cara.mia.pago.empleado'].search([('name', 'ilike', ref)], limit=1)
        
        if not nomina:
            return f"Error: No encontré la nómina '{ref}'."

        # REGLA DE NEGOCIO: Solo se borra si está en borrador o en proceso
        # Validar el nombre del campo estado en tu modelo (puede ser 'state' o 'estado')
        estado_actual = nomina.state if hasattr(nomina, 'state') else nomina.estado
        if estado_actual not in ['draft', 'in_progress', 'borrador', 'en_proceso']:
            return f"Error: La nómina {nomina.name} está en estado '{estado_actual}'. Solo se permite eliminar nóminas que estén en Borrador o En Proceso."

        # MAGIA DE CONFIRMACIÓN PARA LA IA
        if not confirmado:
            return f"⚠️ ATENCIÓN: Encontré la nómina '{nomina.name}'. Esta acción la borrará permanentemente del sistema. Pídele al usuario que confirme explícitamente si desea eliminarla. Si acepta, vuelve a llamar a esta herramienta con 'confirmado' en true."

        nombre_eliminado = nomina.name
        nomina.unlink()
        return f"Éxito: La nómina '{nombre_eliminado}' ha sido eliminada."
    except Exception as e:
        return f"Error al borrar la nómina: {str(e)}"


def ejecutar_generar_liquidacion(env, parametros):
    try:
        # 1. Crear documento de liquidación con la fecha de hoy
        nueva_liq = env['cara.mia.liquidacion'].create({})
        
        # 2. Llamar a tu función masiva
        respuesta = nueva_liq.action_cargar_todos_empleados()
        
        # Tu función devuelve un diccionario (notificación cliente) si no hay empleados para liquidar
        if isinstance(respuesta, dict) and respuesta.get('type') == 'ir.actions.client':
            nueva_liq.unlink()
            return "No se generó la liquidación masiva porque ningún empleado tiene saldo de reserva (0.22%) superior a $0.00."
            
        return f"Éxito: Documento de Liquidación Global '{nueva_liq.name}' creado en estado Borrador. Total acumulado para pagar: ${nueva_liq.total_a_pagar} entre {nueva_liq.cantidad_empleados} empleados. Dile al usuario que revise el borrador en el sistema antes de confirmarlo."
    except Exception as e:
        return f"Error calculando liquidación: {str(e)}"

def ejecutar_actualizar_liquidacion(env, parametros):
    try:
        ref = parametros.get('referencia_liquidacion', '').strip()
        liquidacion = env['cara.mia.liquidacion'].search([('name', 'ilike', ref)], limit=1)
        
        if not liquidacion:
            return f"Error: No encontré la liquidación '{ref}'."
            
        estado_actual = liquidacion.state if hasattr(liquidacion, 'state') else liquidacion.estado
        if estado_actual not in ['draft', 'borrador']:
             return f"Error: La liquidación ya está en estado '{estado_actual}', no se puede modificar."

        valores = {}
        if parametros.get('observaciones'):
            valores['observaciones'] = parametros.get('observaciones')

        if not valores:
            return "Aviso: No se enviaron datos para actualizar la liquidación."

        liquidacion.write(valores)
        return f"Éxito: Liquidación '{liquidacion.name}' actualizada."
    except Exception as e:
        return f"Error al actualizar la liquidación: {str(e)}"

def ejecutar_borrar_liquidacion(env, parametros):
    try:
        ref = parametros.get('referencia_liquidacion', '').strip()
        confirmado = parametros.get('confirmado', False)

        liquidacion = env['cara.mia.liquidacion'].search([('name', 'ilike', ref)], limit=1)
        
        if not liquidacion:
            return f"Error: No encontré la liquidación '{ref}'."

        # REGLA DE NEGOCIO ESTRICTA: Solo en borrador
        estado_actual = liquidacion.state if hasattr(liquidacion, 'state') else liquidacion.estado
        if estado_actual not in ['draft', 'borrador']:
            return f"Error: La liquidación {liquidacion.name} está en estado '{estado_actual}'. Por regla de negocio, SOLO se pueden eliminar liquidaciones en estado Borrador."

        # MAGIA DE CONFIRMACIÓN PARA LA IA
        if not confirmado:
            return f"⚠️ ATENCIÓN: Encontré la liquidación '{liquidacion.name}'. Pídele al usuario que confirme explícitamente si desea eliminarla. Si acepta, vuelve a llamar a esta herramienta con 'confirmado' en true."

        nombre_eliminado = liquidacion.name
        liquidacion.unlink()
        return f"Éxito: La liquidación '{nombre_eliminado}' ha sido eliminada de forma definitiva."
    except Exception as e:
        return f"Error al borrar la liquidación: {str(e)}"