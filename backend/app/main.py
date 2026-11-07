import os
from fastapi import FastAPI
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "")
    app_env: str = os.getenv("APP_ENV", "dev")

settings = Settings()
app = FastAPI(title="Uitrix CRM API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}

@app.get("/")
def root():
    return {"service": "uitrix-crm", "message": "API is alive"}
