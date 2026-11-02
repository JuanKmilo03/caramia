import json

def ejecutar_crear_cotizacion(env, parametros):
    try:
        cliente_nombre = parametros.get('nombre_cliente', '')
        modelo_ref = parametros.get('modelo_existente', '')
        modelo_nuevo = parametros.get('modelo_nuevo', '')
        
        valores = {
            'tipo_lote': parametros.get('tipo_lote', '12'),
            'precio_venta_par': parametros.get('precio_venta_esperado', 0.0),
            'observaciones': 'Cotización generada por Inteligencia Artificial.'
        }

        # Vincular Cliente si existe
        if cliente_nombre:
            cliente = env['cara.mia.cliente'].search([('name', 'ilike', cliente_nombre)], limit=1)
            if cliente:
                valores['cliente_id'] = cliente.id

        # Si se basan en una referencia existente, hay que copiarle la "receta" (materiales y labores)
        # Esto simula tu maravilloso @api.onchange('referencia_id')
        if modelo_ref:
            referencia = env['cara.mia.referencia'].search([('nombre_modelo', 'ilike', modelo_ref)], limit=1)
            if referencia:
                valores['referencia_id'] = referencia.id
                
                # Simulamos la copia de insumos
                lote = 12 if valores['tipo_lote'] == '12' else 24
                mat_lines = []
                for ins in referencia.insumo_ids:
                    if ins.insumo_catalogo_id:
                        mat_lines.append((0, 0, {
                            'insumo_catalogo_id': ins.insumo_catalogo_id.id,
                            'tipo_componente_id': ins.insumo_catalogo_id.tipo_componente_id.id or False,
                            'unidad_medida': ins.unidad_medida,
                            'cantidad_docena': ins.cantidad * lote,
                            'precio_unitario': ins.insumo_catalogo_id.costo_referencia or 0.0
                        }))
                valores['material_ids'] = mat_lines
                
                # Simulamos la copia de labores
                lab_lines = []
                for lab in referencia.labor_ids:
                    if lab.tipo_labor_id:
                        lab_lines.append((0, 0, {
                            'tipo_labor_id': lab.tipo_labor_id.id,
                            'costo_par': lab.tarifa_pago or 0.0
                        }))
                valores['labor_ids'] = lab_lines

        elif modelo_nuevo:
            valores['nombre_modelo'] = modelo_nuevo

        # Creamos la cotización
        nueva_cot = env['caramia.costo'].create(valores)
        
        mensaje = f"Éxito: Se ha creado la cotización {nueva_cot.name}."
        if modelo_ref and 'referencia_id' in valores:
            mensaje += f" Se copió la receta del modelo '{referencia.nombre_modelo}'. Costo de producción calculado: ${nueva_cot.costo_total_par} por par."
        else:
            mensaje += " Es una cotización en blanco. Dile al usuario que debe ir al sistema a agregar los materiales y labores a mano."
            
        return mensaje
        
    except Exception as e:
        return f"Error al crear cotización: {str(e)}"


def ejecutar_consultar_rentabilidad(env, parametros):
    try:
        codigo = parametros.get('numero_cotizacion').strip().upper()
        cot = env['caramia.costo'].search([('name', '=', codigo)], limit=1)
        
        if not cot:
            return f"Error: No encontré la cotización '{codigo}'."
            
        info = {
            "cliente": cot.cliente_id.name if cot.cliente_id else "Sin asignar",
            "modelo": cot.referencia_id.nombre_modelo if cot.referencia_id else cot.nombre_modelo,
            "costo_materiales_par": cot.total_materiales_par,
            "costo_mano_obra_par": cot.total_labores_par,
            "costo_total_produccion_par": cot.costo_total_par,
            "precio_venta_sugerido": cot.precio_venta_par,
            "ganancia_neta_par": cot.margen_ganancia,
            "estado_actual": cot.state
        }
        
        return f"Análisis de rentabilidad de {codigo}: {json.dumps(info)}"
    except Exception as e:
        return f"Error leyendo cotización: {str(e)}"


def ejecutar_aprobar_cotizacion(env, parametros):
    try:
        codigo = parametros.get('numero_cotizacion').strip().upper()
        cot = env['caramia.costo'].search([('name', '=', codigo)], limit=1)
        
        if not cot:
            return f"Error: No encontré la cotización '{codigo}'."
            
        if cot.state == 'production':
            return f"La cotización {codigo} ya fue aprobada y tiene la Orden de Producción {cot.production_id.name} asignada."
            
        if not cot.cliente_id:
            return "Error de negocio: Odoo exige que la cotización tenga un cliente asignado antes de poder pasar a producción."
            
        if not cot.referencia_id:
            return "Error de negocio: El modelo es nuevo y no tiene referencia oficial. Dile al usuario que debe ir a Odoo y darle click al botón 'Pasar a Producción' para que el sistema le abra la ventana de guardado de la nueva referencia."

        # Todo está bien, ejecutamos tu función interna
        respuesta = cot._crear_orden_produccion()
        
        return f"Éxito total: La cotización {codigo} ha sido aprobada. Se generó automáticamente la Orden de Producción {cot.production_id.name} en la fábrica."
        
    except Exception as e:
        error_limpio = str(e).replace('\n', ' ')
        return f"Odoo impidió el pase a producción: {error_limpio}"