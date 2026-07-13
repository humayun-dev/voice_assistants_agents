from fastapi import FastAPI
from app.api.webhook import router as webhook_router

app = FastAPI(title="WhatsApp Business Agent")

app.include_router(webhook_router)


@app.get("/")
def health_check():
    return {"status": "alive"}
