from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.websocket import router as ws_router

app = FastAPI(title="Gemini Voice Assistant")

app.include_router(ws_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
    return {"status": "server running"}