ENTIDADES = {
    "empleado": {
        "modelo": "cara.mia.empleado",
        "ayuda": (
            "Empleados de la fábrica. 'empleado_id' es la CÉDULA (texto), NO el ID interno. "
            "El ID interno es 'id'. 'tipo_labor_id' es el ID numérico de un registro de la "
            "entidad 'tipo_labor' (búscalo antes de crear). 'total_prestamos_pendientes' es solo lectura."
        ),
        "campos_lectura": ["id", "empleado_id", "nombre_empleado", "telefono_empleado",
                           "tipo_labor_id", "pago_liquidado", "total_prestamos_pendientes"],
        "campos_escritura": ["empleado_id", "nombre_empleado", "telefono_empleado",
                             "tipo_labor_id", "pago_liquidado"],
        "requeridos": ["empleado_id", "nombre_empleado", "telefono_empleado", "tipo_labor_id"],
        "permisos": {"leer", "crear", "editar"},
    },
    "prestamo": {
        "modelo": "cara.mia.prestamo",
        "ayuda": (
            "Préstamos/descuentos de un empleado. Aquí 'empleado_id' es el ID INTERNO (campo 'id') "
            "del empleado, NO la cédula. 'state': 'pending' (En Deuda) o 'paid' (Pagado). "
            "'fecha' en formato YYYY-MM-DD (si no se indica, se usa hoy). 'monto' es numérico."
        ),
        "campos_lectura": ["id", "empleado_id", "fecha", "monto", "observaciones", "state"],
        "campos_escritura": ["empleado_id", "fecha", "monto", "observaciones", "state"],
        "requeridos": ["empleado_id", "monto"],
        "permisos": {"leer", "crear", "editar"},
    },
    "tipo_labor": {
        "modelo": "cara.mia.tipo.labor",
        "ayuda": "Catálogo de labores. Solo lectura.",
        "campos_lectura": ["id", "name"],   # AJUSTA al campo real de tu modelo
        "campos_escritura": [],
        "requeridos": [],
        "permisos": {"leer"},
    },
}


def catalogo() -> str:
    lineas = []
    for nombre, cfg in ENTIDADES.items():
        lineas.append(
            f"- {nombre}: {cfg['ayuda']} "
            f"Campos: {', '.join(cfg['campos_lectura'])}. "
            f"Permisos: {', '.join(sorted(cfg['permisos']))}."
        )
    return "\n".join(lineas)
