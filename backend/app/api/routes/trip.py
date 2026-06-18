from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.trip import Trip
from app.schemas.trip import TripResponse
from datetime import datetime

router = APIRouter()

@router.get("", response_model=list[TripResponse])
async def list_trips(
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_distance: float | None = None,
    max_distance: float | None = None,
    limit: int = Query(100, le=1000),
    offset: int = 0
    ):
    statement = select(Trip)
    if start_date:
        statement = statement.where(Trip.pickup_datetime >= start_date)
    if end_date:
        statement = statement.where(Trip.pickup_datetime < end_date)
    if min_distance is not None:
        statement = statement.where(Trip.trip_distance >= min_distance)
    if max_distance is not None:
        statement = statement.where(Trip.trip_distance <= max_distance)

    statement = statement.order_by(Trip.pickup_datetime).limit(limit).offset(offset)

    rows = (await db.execute(statement)).scalars().all()
    return rows
