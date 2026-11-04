import os
os.environ.setdefault("AGENT_SECRET", "testsecret")
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
SECRET = os.environ["AGENT_SECRET"]

def test_health():
    r = client.get("/")
    assert r.status_code == 200

def test_chat_requires_secret():
    r = client.post("/api/chat", json={"mensaje": "hola", "user_id": 1})
    assert r.status_code == 401

def test_chat_with_secret_ok(monkeypatch):
    import agent
    async def fake_procesar_chat(mensaje, user_id):
        return {"tipo": "texto", "respuesta": "ok"}
    monkeypatch.setattr(agent, "procesar_chat", fake_procesar_chat)
    r = client.post("/api/chat", json={"mensaje": "hola", "user_id": 1}, headers={"X-Agent-Secret": SECRET})
    assert r.status_code == 200
    assert r.json()["respuesta"] == "ok"