# Módulo: ai_actions/dispatcher.py

# Importamos las funciones de nuestros especialistas
from .clientes_actions import ejecutar_crear_cliente, ejecutar_consultar_clientes

# EL MAPA DE ACCIONES (Cuando FastAPI mande una orden, aquí sabemos qué función usar)
MAPA_ACCIONES = {
    "crear_cliente": ejecutar_crear_cliente,
    "consultar_clientes": ejecutar_consultar_clientes,
    # Mañana añadirás: "crear_factura": ejecutar_crear_factura
}

def procesar_accion_ia(env, accion, parametros):
    """
    Recibe la sesión de Odoo (env), el nombre de la acción y los datos.
    Busca en el mapa y ejecuta la función correspondiente.
    """
    if accion in MAPA_ACCIONES:
        funcion_especialista = MAPA_ACCIONES[accion]
        # Ejecutamos la función y devolvemos su resultado
        return funcion_especialista(env, parametros)
    else:
        return f"Acción desconocida o no programada en el despachador: {accion}"