from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .odoo_client import odoo_db
# import openai  # Lo usaremos en el siguiente paso

app = FastAPI(title="Agente IA - Cara Mia")

# Modelo de datos que esperamos recibir del usuario
class ChatRequest(BaseModel):
    user_id: int
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    user_msg = request.message
    
    # ---------------------------------------------------------
    # AQUÍ IRÁ LA LÓGICA DEL AGENTE IA (LangChain / OpenAI)
    # Por ahora, haremos una prueba simple consultando Odoo
    # ---------------------------------------------------------
    
    try:
        # Ejemplo: Si el usuario dice algo, probamos conexión buscando un socio
        # (Esto es solo para probar que OdooClient funciona)
        partners = odoo_db.search_read('res.partner', [], ['name'])
        total_partners = len(partners)
        
        # Respuesta simulada del agente
        respuesta_ia = f"Recibí tu mensaje: '{user_msg}'. Conexión exitosa a Odoo. Tienes {total_partners} contactos en la base de datos."
        
        return {"reply": respuesta_ia}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Servicio FastAPI corriendo"}