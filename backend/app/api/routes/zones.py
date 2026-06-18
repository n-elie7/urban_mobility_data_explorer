from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_zone_or_404
from app.models.zone import TaxiZone
from app.schemas.zone import ZoneResponse

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/", response_model=list[ZoneResponse])
async def list_zones(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(TaxiZone).order_by(TaxiZone.location_id))
    return result.scalars().all()


@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone: TaxiZone = Depends(get_zone_or_404)):
    return zone