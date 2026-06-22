from fastapi import FastAPI

from app.api.routes import analytics, health, trip, zones
from .core.logging import configure_logging
from .core.config import get_settings
from fastapi.middleware.cors import CORSMiddleware

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.api_title, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(zones.router, prefix="/api/zones", tags=["zones"])
app.include_router(trip.router, prefix="/api/trips", tags=["trips"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
def root():
    return {"service": settings.api_title, "docs": "/docs"}
