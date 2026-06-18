from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db

router = APIRouter()

@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """function that checks health of an API"""
    db_ok, postgis = False, None
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
        response = await db.execute(text("SELECT PostGIS_Version()"))
        postgis = response.scalar()
    except Exception:
        pass
    return {"status": "ok", "database": db_ok, "postgis": postgis}
