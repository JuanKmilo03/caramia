import sys, os
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base)
from ai_actions.dispatcher import MAPA_ACCIONES

def test_dispatcher_has_actions():
    assert len(MAPA_ACCIONES) >= 30
    assert "crear_cliente" in MAPA_ACCIONES
    assert "eliminar_cliente" in MAPA_ACCIONES