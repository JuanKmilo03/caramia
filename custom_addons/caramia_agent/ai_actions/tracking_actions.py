import json

def ejecutar_consultar_progreso(env, parametros):
    try:
        codigo = parametros.get('codigo_orden').strip().upper()
        orden = env['cara.mia.produccion'].search([('name', '=', codigo)], limit=1)
        
        if not orden:
            return f"Error: La orden {codigo} no existe."
            
        info = {
            "orden": orden.name,
            "estado_general": orden.state,
            "cliente": orden.cliente_id.name if orden.cliente_id else "N/A",
            "modelo": orden.referencia_id.nombre_modelo if orden.referencia_id else "N/A",
            "total_pares": orden.total_pares,
            "porcentaje_progreso": f"{round(orden.progreso, 2)}%",
            "labor_actual_o_siguiente": orden.cargo_actual,
            "dias_transcurridos": orden.dias_transcurridos,
            "esta_estancada": orden.esta_estancada,
            "motivo_estancamiento": orden.motivo_estancamiento if orden.esta_estancada else "Ninguno"
        }
        return f"Progreso de {codigo}: {json.dumps(info)}"
    except Exception as e:
        return f"Error consultando progreso: {str(e)}"

def ejecutar_consultar_tablero(env, parametros):
    try:
        # Llamamos directamente a tu tremenda función del dashboard
        datos_dashboard = env['cara.mia.produccion'].get_tracking_dashboard()
        
        resumen_limpio = {
            "pares_procesados_semana": datos_dashboard['semana']['procesado'],
            "pares_programados_semana": datos_dashboard['semana']['programado'],
            "ordenes_activas_en_planta": datos_dashboard['activas'],
            "ordenes_estancadas_problema": datos_dashboard['estancadas'],
            "ordenes_vencidas": datos_dashboard['entregas']['vencidas'],
            "pares_totales_pendientes": datos_dashboard['entregas']['pendientes_pares']
        }
        
        return f"Resumen gerencial de la fábrica: {json.dumps(resumen_limpio)}"
    except Exception as e:
        return f"Error leyendo el tablero: {str(e)}"

def ejecutar_listar_estancadas(env, parametros):
    try:
        ordenes = env['cara.mia.produccion'].search([('esta_estancada', '=', True), ('state', 'in', ['draft', 'in_progress', 'stopped'])])
        
        if not ordenes:
            return "Excelentes noticias: En este momento no hay ninguna orden de producción estancada en la fábrica."
            
        lista = []
        for o in ordenes:
            lista.append(f"- {o.name} (Cliente: {o.cliente_id.name}): {o.motivo_estancamiento} | Progreso: {round(o.progreso)}%")
            
        texto_final = "\n".join(lista)
        return f"Atención. Se encontraron {len(ordenes)} órdenes estancadas:\n{texto_final}"
    except Exception as e:
        return f"Error buscando estancadas: {str(e)}"

def ejecutar_cambiar_estado(env, parametros):
    try:
        codigo = parametros.get('codigo_orden').strip().upper()
        accion = parametros.get('accion')
        
        orden = env['cara.mia.produccion'].search([('name', '=', codigo)], limit=1)
        if not orden:
            return f"Error: La orden {codigo} no existe."
            
        if accion == 'detener':
            if orden.state == 'stopped':
                return f"La orden {codigo} ya se encuentra detenida."
            orden.action_set_stopped()
            return f"La orden {codigo} ha sido DETENIDA manualmente."
            
        elif accion == 'reanudar':
            if orden.state == 'in_progress':
                return f"La orden {codigo} ya se encuentra en proceso."
            orden.action_resume()
            return f"La orden {codigo} ha sido REANUDADA y vuelve a estar 'En Proceso'."
            
    except Exception as e:
        return f"Error cambiando estado: {str(e)}"