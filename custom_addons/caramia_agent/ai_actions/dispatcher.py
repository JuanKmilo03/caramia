import logging

from .clientes_actions import (
    ejecutar_crear_cliente, 
    ejecutar_consultar_clientes, 
    ejecutar_actualizar_cliente,
    ejecutar_eliminar_cliente
)

from .empleados_actions import (
    ejecutar_crear_empleado,
    ejecutar_consultar_empleados,
    ejecutar_eliminar_empleado,
    ejecutar_registrar_prestamo
)

from .produccion_actions import (
    ejecutar_crear_orden,
    ejecutar_consultar_ordenes,
    ejecutar_cambiar_estado_orden
)

from .referencias_actions import (
    ejecutar_crear_referencia,
    ejecutar_consultar_referencia,
    ejecutar_editar_referencia,
    ejecutar_eliminar_referencia
)

from .catalogos_insumo_labores_actions import (
    ejecutar_crear_tipo_labor,
    ejecutar_consultar_labores,
    ejecutar_actualizar_labor,
    ejecutar_borrar_labor,

    ejecutar_crear_insumo,
    ejecutar_consultar_insumos,
    ejecutar_actualizar_insumo,
    ejecutar_borrar_insumo
)

from .empleado_nomina_liquidacion_actions import (
    ejecutar_registrar_tiquete,
    ejecutar_generar_nomina,
    ejecutar_actualizar_nomina,
    ejecutar_borrar_nomina,
    ejecutar_generar_liquidacion,
    ejecutar_actualizar_liquidacion,
    ejecutar_borrar_liquidacion,
)

from .facturacion_actions import (
    ejecutar_crear_factura,
    ejecutar_actualizar_factura,
    ejecutar_emitir_factura,
    ejecutar_consultar_factura
)

from .tracking_actions import (
    ejecutar_consultar_progreso,
    ejecutar_consultar_tablero,
    ejecutar_listar_estancadas,
    ejecutar_cambiar_estado,
)

from .costos_actions import (
    ejecutar_crear_cotizacion,
    ejecutar_consultar_rentabilidad,
    ejecutar_aprobar_cotizacion
)

from .feedback_actions import ejecutar_guardar_correccion
# EL MAPA DE ACCIONES (Cuando FastAPI mande una orden, aquí sabemos qué función usar)
MAPA_ACCIONES = {
    #Clientes
    "crear_cliente": ejecutar_crear_cliente,
    "consultar_clientes": ejecutar_consultar_clientes,
    "actualizar_cliente": ejecutar_actualizar_cliente,
    "eliminar_cliente": ejecutar_eliminar_cliente,

    #Empleados
    "crear_empleado": ejecutar_crear_empleado,
    "consultar_empleados": ejecutar_consultar_empleados,
    "eliminar_empleado": ejecutar_eliminar_empleado,
    "registrar_prestamo": ejecutar_registrar_prestamo,

    #Producción
    "crear_orden_produccion": ejecutar_crear_orden,
    "consultar_ordenes_produccion": ejecutar_consultar_ordenes,
    "cambiar_estado_orden_produccion": ejecutar_cambiar_estado_orden,

    #Referencias
    "crear_referencia": ejecutar_crear_referencia,
    "consultar_referencia": ejecutar_consultar_referencia,
    "editar_referencia": ejecutar_editar_referencia,
    "eliminar_referencia": ejecutar_eliminar_referencia,

    #Catalogos de insumos y labores
    "crear_tipo_labor": ejecutar_crear_tipo_labor,
    "consultar_labores": ejecutar_consultar_labores,
    "actualizar_labor": ejecutar_actualizar_labor,
    "borrar_labor": ejecutar_borrar_labor,

    "crear_insumo": ejecutar_crear_insumo,
    "consultar_insumos": ejecutar_consultar_insumos,
    "actualizar_insumo": ejecutar_actualizar_insumo,
    "borrar_insumo": ejecutar_borrar_insumo,
    

    #Operaciones de nómina y liquidación
    "registrar_tiquete_trabajo": ejecutar_registrar_tiquete,
    "generar_nomina": ejecutar_generar_nomina,
    "actualizar_nomina": ejecutar_actualizar_nomina,
    "borrar_nomina": ejecutar_borrar_nomina,
    "generar_liquidacion": ejecutar_generar_liquidacion,
    "actualizar_liquidacion": ejecutar_actualizar_liquidacion,
    "borrar_liquidacion": ejecutar_borrar_liquidacion,
    

    #Facturación
    "crear_factura": ejecutar_crear_factura,
    "actualizar_factura_borrador": ejecutar_actualizar_factura,
    "emitir_factura": ejecutar_emitir_factura,
    "consultar_factura": ejecutar_consultar_factura,
    
    #Tracking
    "consultar_progreso_orden": ejecutar_consultar_progreso,
    "consultar_tablero_produccion": ejecutar_consultar_tablero,
    "listar_ordenes_estancadas": ejecutar_listar_estancadas,
    "cambiar_estado_orden_manual": ejecutar_cambiar_estado,

    #Costos
    "crear_cotizacion_base": ejecutar_crear_cotizacion,
    "consultar_rentabilidad_cotizacion": ejecutar_consultar_rentabilidad,
    "aprobar_cotizacion_a_produccion": ejecutar_aprobar_cotizacion,

    #Feedback
    "guardar_correccion": ejecutar_guardar_correccion

}

_logger = logging.getLogger("caramia.agent")

def _registrar_log(env, accion, parametros, resultado, exito):
    try:
        if 'caramia.agent.log' in env:
            env['caramia.agent.log'].sudo().create({
                'accion': accion,
                'parametros': str(parametros),
                'resultado': str(resultado)[:4000],
                'exito': bool(exito),
            })
    except Exception:
        pass

def procesar_accion_ia(env, accion, parametros):
    """
    Recibe la sesión de Odoo (env), el nombre de la acción y los datos.
    Busca en el mapa y ejecuta la función correspondiente.
    """
    uid = getattr(env, "uid", None)
    _logger.info("IA accion=%s uid=%s params=%s", accion, uid, parametros)
    if accion in MAPA_ACCIONES:
        funcion_especialista = MAPA_ACCIONES[accion]
        try:
            resultado = funcion_especialista(env, parametros)
            _logger.info("IA accion=%s resultado=%s", accion, str(resultado)[:500])
            _registrar_log(env, accion, parametros, resultado, True)
            return resultado
        except Exception as e:
            _logger.exception("IA accion=%s error", accion)
            _registrar_log(env, accion, parametros, str(e), False)
            return f"Error ejecutando '{accion}': {str(e)}"
    else:
        _logger.warning("IA accion desconocida=%s", accion)
        return f"Acción desconocida o no programada en el despachador: {accion}"