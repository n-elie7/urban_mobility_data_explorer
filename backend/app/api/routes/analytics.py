from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.trip import Trip

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db_session)):
    stmt = select(
        func.count(Trip.trip_id).label("total_trips"),
        func.avg(Trip.fare_amount).label("avg_fare"),
        func.avg(Trip.trip_distance).label("avg_distance"),
    )
    result = await db.execute(stmt)
    row = result.one()
    return {
        "total_trips": row.total_trips,
        "avg_fare": round(float(row.avg_fare), 2) if row.avg_fare else None,
        "avg_distance": round(float(row.avg_distance), 2) if row.avg_distance else None,
    }