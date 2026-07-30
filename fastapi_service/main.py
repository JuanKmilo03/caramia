from fastapi import FastAPI

app = FastAPI(title="Cara Mia AI Service")

@app.get("/")
def read_root():
    return {"status": "Asistente de IA Cara Mia activo y listo"}