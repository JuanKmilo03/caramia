
from .clientes_tools import HERRAMIENTAS_CLIENTES
# Ensamblamos TODAS las herramientas en una sola lista gigante
# Esta es la única variable que FastAPI leerá.
TODAS_LAS_HERRAMIENTAS = HERRAMIENTAS_CLIENTES # + HERRAMIENTAS_VENTAS + HERRAMIENTAS_INVENTARIO