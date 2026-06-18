from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.trip import Trip
from app.schemas.trip import TripResponse

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/", response_model=list[TripResponse])
async def list_trips(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Trip).limit(100))
    return result.scalars().all()


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: int, db: AsyncSession = Depends(get_db_session)):
    stmt = select(Trip).where(Trip.trip_id == trip_id)
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    return trip