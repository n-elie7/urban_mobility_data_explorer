from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_zone_or_404
from app.models.zone import TaxiZone
from app.schemas.zone import ZoneResponse

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/", response_model=List[ZoneResponse], summary="List all taxi zones with geometry")

def list_zones(
    db: Session = Depends(get_db_session),
    borough: Optional[str] = Query(None),
    service_zone: Optional[str] = Query(None),
):
    query = db.query(TaxiZone)
    if borough:
        query = query.filter(TaxiZone.borough.ilike(borough))
    if service_zone:
        query = query.filter(TaxiZone.service_zone.ilike(service_zone))
    return query.order_by(TaxiZone.location_id).all()


@router.get("/boroughs", summary="List distinct boroughs")

def list_boroughs(db: Session = Depends(get_db_session)):
    rows = db.query(TaxiZone.borough).distinct().order_by(TaxiZone.borough).all()

    return {"boroughs": [r.borough for r in rows if r.borough]}


@router.get("/{zone_id}", response_model=ZoneResponse, summary="Get a single zone by LocationID")

def get_zone(zone: TaxiZone = Depends(get_zone_or_404)):

    return zone