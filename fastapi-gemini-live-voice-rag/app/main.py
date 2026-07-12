from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.websocket import router as ws_router
from app.services import vector_store

app = FastAPI(title="Gemini Voice Assistant")

app.include_router(ws_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup():
    # Loads the pre-built vector index into memory once, at server
    # startup, rather than on every request. If it hasn't been built
    # yet, this logs a warning and search_leave_rules returns nothing
    # until you run scripts/build_index.py.
    vector_store.load_index()


@app.get("/")
def root():
    return {"status": "server running"}
