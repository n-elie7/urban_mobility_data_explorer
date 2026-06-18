from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.trip import Trip

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/basic")
async def basic_insights(db: AsyncSession = Depends(get_db_session)):
    stmt = select(
        func.count(Trip.trip_id).label("total_trips"),
        func.avg(Trip.fare_amount).label("avg_fare"),
        func.max(Trip.fare_amount).label("max_fare"),
        func.min(Trip.fare_amount).label("min_fare"),
    )
    result = await db.execute(stmt)
    row = result.one()
    return {
        "total_trips": row.total_trips,
        "avg_fare": round(float(row.avg_fare), 2) if row.avg_fare else None,
        "max_fare": round(float(row.max_fare), 2) if row.max_fare else None,
        "min_fare": round(float(row.min_fare), 2) if row.min_fare else None,
    }