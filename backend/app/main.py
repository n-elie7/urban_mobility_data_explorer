from fastapi import FastAPI
from .core.logging import configure_logging
from .core.config import get_settings

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.api_title, version="0.1.0")

@app.get("/")
def root():
    return {"service": settings.api_title, "docs": "/docs"}
