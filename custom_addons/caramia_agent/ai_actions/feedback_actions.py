def ejecutar_guardar_correccion(env, parametros):
    try:
        env['caramia.agent.correction'].create({
            'pregunta': parametros.get('pregunta', ''),
            'correccion': parametros.get('correccion', '')
        })
        return "Correccion guardada para mejorar futuras respuestas."
    except Exception as e:
        return f"Error guardando correccion: {str(e)}"