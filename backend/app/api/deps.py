from fastapi import Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.zone import TaxiZone


class PaginationParams:
    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(default=100, ge=1, le=1000, description="Max records to return"),
    ):
        self.skip = skip
        self.limit = limit


def pagination_params(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)


async def get_zone_or_404(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
) -> TaxiZone:
    result = await db.execute(
        select(TaxiZone).where(TaxiZone.location_id == zone_id)
    )
    zone = result.scalar_one_or_none()
    
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

    return zone


def get_db_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    
    return db