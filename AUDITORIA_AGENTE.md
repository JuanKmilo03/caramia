# Auditoria del agente IA (Odoo 18)

## Cambios aplicados

- Eliminado codigo muerto: `ai_service.py`, `herramientas.py`, `entidades.py` (usaban `odoo_client` inexistente).
- Seguridad: secreto compartido `AGENT_SECRET` validado por FastAPI (`X-Agent-Secret`) y enviado desde Odoo; URLs configurables por entorno.
- Timeouts en llamadas HTTP Odoo -> FastAPI.
- Confirmaciones: patron `confirmado` extendido a `eliminar_empleado` y `eliminar_referencia` (ya existia en otros deletes).
- Whitelist de campos en `ejecutar_crear_cliente` (evita mass assignment).
- `confirmar_accion` usa `tool_choice="none"` para evitar nuevas tool calls.
- `optimizar_tokens` mas seguro (no deja mensajes `tool` huerfanos).
- Auditoria: logging en dispatcher (accion, uid, params, resultado, errores).
- Templates: creado `pantalla_chat_ia` y registrado en manifest junto con `assets.xml`.
- Tests basicos: `fastapi_service/tests/test_tools.py`, `tests_dispatcher.py`.

## Riesgos restantes / recomendaciones

- La accion se ejecuta en Odoo antes de la confirmacion del usuario; solo los deletes usan `confirmado`. Considerar preview + confirmacion para create/update criticos.
- FastAPI confia en `user_id` del payload; el secreto compartido mitiga acceso externo pero no suplantacion entre usuarios. Ideal: validar usuario via Odoo (session/token) o mover orquestacion al modulo.
- Sin streaming ni manejo de multiples tool_calls (se toma solo el primero).
- Sin tests de integracion end-to-end (requieren Odoo + Groq).
- Modelo LLM con tool calling variable; evaluar modelos con function calling robusto.
- Agregar rate limiting y persistencia de auditoria en BD si se requiere trazabilidad formal.