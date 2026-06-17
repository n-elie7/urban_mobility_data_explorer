from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_db_session, pagination_params, PaginationParams
from app.models.trip import Trip
from app.models.zone import TaxiZone
from app.schema.trip import TripResponse

router = APIRouter(prefix="/trips", tags=["trips"])


async def _build_trip_filters(
    pickup_date_from: Optional[date],
    pickup_date_to: Optional[date],
    distance_min: Optional[float],
    distance_max: Optional[float],
    fare_min: Optional[float],
    fare_max: Optional[float],
    borough: Optional[str],
):
    filters = []
    if pickup_date_from:
        filters.append(Trip.pickup_datetime >= pickup_date_from)
    if pickup_date_to:
        filters.append(Trip.pickup_datetime <= pickup_date_to)
    if distance_min is not None:
        filters.append(Trip.trip_distance >= distance_min)
    if distance_max is not None:
        filters.append(Trip.trip_distance <= distance_max)
    if fare_min is not None:
        filters.append(Trip.fare_amount >= fare_min)
    if fare_max is not None:
        filters.append(Trip.fare_amount <= fare_max)
    if airport_only is not None:
        filters.append(Trip.is_airport_trip == airport_only)
    if borough:
        pu_zone = db.query(TaxiZone.location_id).filter(
            TaxiZone.borough.ilike(borough)
        ).subquery()
        filters.append(Trip.pu_location_id.in_(pu_zone))
    return filters


@router.get("/", response_model=List[TripResponse], summary="List taxi trips with optional filters")
def list_trips(
    db: Session = Depends(get_db_session),
    pagination: PaginationParams = Depends(pagination_params),
    pickup_date_from: Optional[date] = Query(None),
    pickup_date_to: Optional[date] = Query(None),
    distance_min: Optional[float] = Query(None, ge=0),
    distance_max: Optional[float] = Query(None, ge=0),
    fare_min: Optional[float] = Query(None, ge=0),
    fare_max: Optional[float] = Query(None, ge=0),
    borough: Optional[str] = Query(None),
    airport_only: Optional[bool] = Query(None),
):
    filters = _build_trip_filters(
        db, pickup_date_from, pickup_date_to,
        distance_min, distance_max,
        fare_min, fare_max,
        borough, airport_only,
    )
    return (
        db.query(Trip)
        .filter(and_(*filters))
        .order_by(Trip.tpep_pickup_datetime.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )


@router.get("/count", summary="Count trips matching filters")
def count_trips(
    db: Session = Depends(get_db_session),
    pickup_date_from: Optional[date] = Query(None),
    pickup_date_to: Optional[date] = Query(None),
    distance_min: Optional[float] = Query(None, ge=0),
    distance_max: Optional[float] = Query(None, ge=0),
    fare_min: Optional[float] = Query(None, ge=0),
    fare_max: Optional[float] = Query(None, ge=0),
    borough: Optional[str] = Query(None),
    airport_only: Optional[bool] = Query(None),
):
    filters = _build_trip_filters(
        db, pickup_date_from, pickup_date_to,
        distance_min, distance_max,
        fare_min, fare_max,
        borough, airport_only,
    )
    return {"count": db.query(Trip).filter(and_(*filters)).count()}


@router.get("/{trip_id}", response_model=TripResponse, summary="Get a single trip by ID")
def get_trip(trip_id: int, db: Session = Depends(get_db_session)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    return trip