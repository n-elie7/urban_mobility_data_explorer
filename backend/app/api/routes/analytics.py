from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract

from app.api.deps import get_db_session
from app.models.trip import Trip
from app.models.zone import TaxiZone
from app.schemas.analytics import (
    HourlyDemandItem, FareBucketItem, TopRouteItem,
    BoroughFareItem, DurationDistanceItem,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _date_filters(date_from, date_to):
    filters = []
    if date_from:
        filters.append(Trip.tpep_pickup_datetime >= date_from)
    if date_to:
        filters.append(Trip.tpep_pickup_datetime <= date_to)
    return filters


@router.get("/hourly-demand", response_model=List[HourlyDemandItem])
def hourly_demand(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    borough: Optional[str] = Query(None),
):
    filters = _date_filters(date_from, date_to)
    if borough:
        pu_ids = db.query(TaxiZone.location_id).filter(
            TaxiZone.borough.ilike(borough)
        ).subquery()
        filters.append(Trip.pu_location_id.in_(pu_ids))

    hour_col = extract("hour", Trip.tpep_pickup_datetime).label("hour")
    rows = (
        db.query(hour_col, func.count(Trip.id).label("trip_count"))
        .filter(*filters)
        .group_by(hour_col)
        .order_by(hour_col)
        .all()
    )
    return [{"hour": int(r.hour), "trip_count": r.trip_count} for r in rows]


@router.get("/fare-distribution", response_model=List[FareBucketItem])
def fare_distribution(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bucket_size: float = Query(default=5.0, gt=0),
):
    filters = _date_filters(date_from, date_to)
    bucket_expr = (func.floor(Trip.fare_amount / bucket_size) * bucket_size).label("bucket_floor")
    rows = (
        db.query(bucket_expr, func.count(Trip.id).label("trip_count"))
        .filter(*filters, Trip.fare_amount >= 0)
        .group_by(bucket_expr)
        .order_by(bucket_expr)
        .all()
    )
    return [
        {
            "bucket_label": f"${r.bucket_floor:.0f}–${r.bucket_floor + bucket_size:.0f}",
            "bucket_floor": float(r.bucket_floor),
            "trip_count": r.trip_count,
        }
        for r in rows
    ]


@router.get("/top-routes", response_model=List[TopRouteItem])
def top_routes(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    top_n: int = Query(default=10, ge=1, le=50),
):
    filters = _date_filters(date_from, date_to)
    PU = TaxiZone.__table__.alias("pu_zone")
    DO = TaxiZone.__table__.alias("do_zone")
    rows = (
        db.query(
            Trip.pu_location_id, Trip.do_location_id,
            PU.c.zone.label("pu_zone_name"), PU.c.borough.label("pu_borough"),
            DO.c.zone.label("do_zone_name"), DO.c.borough.label("do_borough"),
            func.count(Trip.id).label("trip_count"),
            func.avg(Trip.fare_amount).label("avg_fare"),
        )
        .join(PU, Trip.pu_location_id == PU.c.location_id, isouter=True)
        .join(DO, Trip.do_location_id == DO.c.location_id, isouter=True)
        .filter(*filters)
        .group_by(
            Trip.pu_location_id, Trip.do_location_id,
            PU.c.zone, PU.c.borough, DO.c.zone, DO.c.borough,
        )
        .order_by(func.count(Trip.id).desc())
        .limit(top_n)
        .all()
    )
    return [
        {
            "pu_location_id": r.pu_location_id,
            "do_location_id": r.do_location_id,
            "pu_zone_name": r.pu_zone_name, "pu_borough": r.pu_borough,
            "do_zone_name": r.do_zone_name, "do_borough": r.do_borough,
            "trip_count": r.trip_count,
            "avg_fare": round(float(r.avg_fare), 2) if r.avg_fare else None,
        }
        for r in rows
    ]


@router.get("/avg-fare-by-borough", response_model=List[BoroughFareItem])
def avg_fare_by_borough(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    filters = _date_filters(date_from, date_to)
    rows = (
        db.query(
            TaxiZone.borough,
            func.count(Trip.id).label("trip_count"),
            func.avg(Trip.fare_amount).label("avg_fare"),
            func.avg(Trip.trip_distance).label("avg_distance"),
            func.avg(Trip.trip_duration_min).label("avg_duration_min"),
        )
        .join(TaxiZone, Trip.pu_location_id == TaxiZone.location_id)
        .filter(*filters)
        .group_by(TaxiZone.borough)
        .order_by(func.avg(Trip.fare_amount).desc())
        .all()
    )
    return [
        {
            "borough": r.borough, "trip_count": r.trip_count,
            "avg_fare": round(float(r.avg_fare), 2) if r.avg_fare else None,
            "avg_distance": round(float(r.avg_distance), 2) if r.avg_distance else None,
            "avg_duration_min": round(float(r.avg_duration_min), 1) if r.avg_duration_min else None,
        }
        for r in rows
    ]


@router.get("/duration-vs-distance", response_model=List[DurationDistanceItem])
def duration_vs_distance(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    sample_size: int = Query(default=500, ge=10, le=5000),
):
    filters = _date_filters(date_from, date_to)
    filters += [Trip.trip_distance > 0, Trip.trip_duration_min > 0]
    rows = (
        db.query(
            Trip.id, Trip.trip_distance, Trip.trip_duration_min,
            Trip.fare_amount, Trip.trip_speed_mph,
        )
        .filter(*filters)
        .order_by(func.random())
        .limit(sample_size)
        .all()
    )
    return [
        {
            "trip_id": r.id, "trip_distance": r.trip_distance,
            "trip_duration_min": r.trip_duration_min,
            "fare_amount": r.fare_amount, "trip_speed_mph": r.trip_speed_mph,
        }
        for r in rows
    ]