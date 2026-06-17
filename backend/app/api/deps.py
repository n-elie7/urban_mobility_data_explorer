from typing import Optional
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

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
    p = PaginationParams.__new__(PaginationParams)
    p.skip = skip
    p.limit = limit
    return p


def get_zone_or_404(zone_id: int, db: Session = Depends(get_db)) -> TaxiZone:
    zone = db.query(TaxiZone).filter(TaxiZone.location_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
    return zone


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db