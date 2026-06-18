from typing import Optional
from datetime import date

# need to fix the import for APIRouter, Depends, Query
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract

from app.api.deps import get_db_session
from app.models.trip import Trip
from app.models.zone import TaxiZone
# need the schems insights file
from app.schemas.insights import (
    PeakDemandInsight, FareEfficiencyInsight, AirportPatternInsight,
)

router = APIRouter(prefix="/insights", tags=["insights"])

_DOW_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def filters(date_from, date_to):
    filters = []
    if date_from:
        filters.append(Trip.tpep_pickup_datetime >= date_from)
    if date_to:
        filters.append(Trip.tpep_pickup_datetime <= date_to)
    return filters


@router.get("/peak-demand", response_model=PeakDemandInsight)
def peak_demand(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    f = _base_filters(date_from, date_to)

    hour_col = extract("hour", Trip.tpep_pickup_datetime).label("hour")
    hourly = (
        db.query(hour_col, func.count(Trip.id).label("trip_count"))
        .filter(*f).group_by(hour_col).order_by(hour_col).all()
    )

    dow_col = extract("dow", Trip.tpep_pickup_datetime).label("dow")
    daily = (
        db.query(dow_col, func.count(Trip.id).label("trip_count"))
        .filter(*f).group_by(dow_col).order_by(dow_col).all()
    )

    borough_rows = (
        db.query(TaxiZone.borough, func.count(Trip.id).label("trip_count"))
        .join(TaxiZone, Trip.pu_location_id == TaxiZone.location_id)
        .filter(*f).group_by(TaxiZone.borough)
        .order_by(func.count(Trip.id).desc()).all()
    )

    peak_hour = max(hourly, key=lambda r: r.trip_count, default=None)
    peak_dow  = max(daily,  key=lambda r: r.trip_count, default=None)

    return {
        "hourly_demand": [{"hour": int(r.hour), "trip_count": r.trip_count} for r in hourly],
        "daily_demand": [
            {"day_of_week": int(r.dow), "day_name": _DOW_NAMES[int(r.dow)], "trip_count": r.trip_count}
            for r in daily
        ],
        "demand_by_borough": [{"borough": r.borough, "trip_count": r.trip_count} for r in borough_rows],
        "peak_hour": int(peak_hour.hour) if peak_hour else None,
        "peak_day_name": _DOW_NAMES[int(peak_dow.dow)] if peak_dow else None,
        "top_borough": borough_rows[0].borough if borough_rows else None,
    }


@router.get("/fare-efficiency", response_model=FareEfficiencyInsight)
def fare_efficiency(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    top_n: int = Query(default=10, ge=1, le=50),
):
    f = _base_filters(date_from, date_to) + [Trip.trip_distance > 0, Trip.fare_amount > 0]

    zone_rows = (
        db.query(
            TaxiZone.location_id, TaxiZone.zone, TaxiZone.borough,
            func.avg(Trip.fare_per_mile).label("avg_fare_per_mile"),
            func.count(Trip.id).label("trip_count"),
        )
        .join(TaxiZone, Trip.pu_location_id == TaxiZone.location_id)
        .filter(*f)
        .group_by(TaxiZone.location_id, TaxiZone.zone, TaxiZone.borough)
        .order_by(func.avg(Trip.fare_per_mile).desc())
        .limit(top_n).all()
    )

    hour_col = extract("hour", Trip.tpep_pickup_datetime)
    time_bucket = case(
        (hour_col.between(6, 9),   "Morning Rush (6–9)"),
        (hour_col.between(10, 15), "Midday (10–15)"),
        (hour_col.between(16, 19), "Evening Rush (16–19)"),
        (hour_col.between(20, 23), "Night (20–23)"),
        else_="Overnight (0–5)",
    ).label("time_bucket")

    time_rows = (
        db.query(time_bucket, func.avg(Trip.fare_per_mile).label("avg_fare_per_mile"),
                 func.count(Trip.id).label("trip_count"))
        .filter(*f).group_by(time_bucket)
        .order_by(func.avg(Trip.fare_per_mile).desc()).all()
    )

    return {
        "top_zones_by_fare_per_mile": [
            {
                "location_id": r.location_id, "zone": r.zone, "borough": r.borough,
                "avg_fare_per_mile": round(float(r.avg_fare_per_mile), 2),
                "trip_count": r.trip_count,
            }
            for r in zone_rows
        ],
        "fare_per_mile_by_time": [
            {
                "time_bucket": r.time_bucket,
                "avg_fare_per_mile": round(float(r.avg_fare_per_mile), 2),
                "trip_count": r.trip_count,
            }
            for r in time_rows
        ],
    }


@router.get("/airport-patterns", response_model=AirportPatternInsight)
def airport_patterns(
    db: Session = Depends(get_db_session),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
):
    f = _base_filters(date_from, date_to)

    def _stats(is_airport: bool):
        return db.query(
            func.count(Trip.id).label("trip_count"),
            func.avg(Trip.fare_amount).label("avg_fare"),
            func.avg(Trip.trip_distance).label("avg_distance"),
            func.avg(Trip.trip_duration_min).label("avg_duration_min"),
            func.avg(Trip.tip_amount).label("avg_tip"),
            func.avg(Trip.total_amount).label("avg_total"),
        ).filter(*f, Trip.is_airport_trip == is_airport).one()

    def _fmt(r):
        return {
            "trip_count": r.trip_count,
            "avg_fare":         round(float(r.avg_fare), 2)         if r.avg_fare         else None,
            "avg_distance":     round(float(r.avg_distance), 2)     if r.avg_distance     else None,
            "avg_duration_min": round(float(r.avg_duration_min), 1) if r.avg_duration_min else None,
            "avg_tip":          round(float(r.avg_tip), 2)          if r.avg_tip          else None,
            "avg_total":        round(float(r.avg_total), 2)        if r.avg_total        else None,
        }

    airport = _stats(True)
    regular = _stats(False)

    hour_col = extract("hour", Trip.tpep_pickup_datetime).label("hour")
    airport_hourly = (
        db.query(hour_col, func.count(Trip.id).label("trip_count"))
        .filter(*f, Trip.is_airport_trip == True)  # noqa: E712
        .group_by(hour_col).order_by(hour_col).all()
    )

    total = airport.trip_count + regular.trip_count
    return {
        "airport_trips": _fmt(airport),
        "regular_trips": _fmt(regular),
        "airport_hourly_demand": [{"hour": int(r.hour), "trip_count": r.trip_count} for r in airport_hourly],
        "pct_airport": round(airport.trip_count / total * 100, 2) if total > 0 else 0.0,
    }