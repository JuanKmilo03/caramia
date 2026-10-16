from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import procesar_chat

app = FastAPI(title="API Agente Cara Mia")

class ChatRequest(BaseModel):
    mensaje: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        respuesta = await procesar_chat(request.mensaje)
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "El microservicio del agente está corriendo correctamente."}