import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tools.registry import TODAS_LAS_HERRAMIENTAS

def test_tools_valid():
    assert isinstance(TODAS_LAS_HERRAMIENTAS, (list, tuple))
    assert len(TODAS_LAS_HERRAMIENTAS) > 0
    for t in TODAS_LAS_HERRAMIENTAS:
        assert t["type"] == "function"
        f = t["function"]
        assert "name" in f and "parameters" in f
        json.dumps(f["parameters"])  # serializable

def test_delete_tools_have_confirmado():
    deletes = [t for t in TODAS_LAS_HERRAMIENTAS if t["function"]["name"].startswith(("eliminar","borrar"))]
    for t in deletes:
        props = t["function"]["parameters"].get("properties", {})
        # clientes/empleado/referencia/nomina/liquidacion/borrar tools should expose confirmado
        assert "confirmado" in props, t["function"]["name"]