from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.session import get_db
from app.models.trip import Trip
from app.models.zone import TaxiZone

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)):
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


@router.get("/hourly-demand")
async def hourly_demand(
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    stmt = select(
        Trip.pickup_hour,
        func.count(Trip.trip_id).label("trips"),
        func.avg(Trip.fare_amount).label("avg_fare"),
    )
    if start_date:
        stmt = stmt.where(Trip.pickup_datetime >= start_date)
    if end_date:
        stmt = stmt.where(Trip.pickup_datetime < end_date)
    
    stmt = stmt.group_by(Trip.pickup_hour).order_by(Trip.pickup_hour)
    result = await db.execute(stmt)
    return [
        {"pickup_hour": row.pickup_hour, "trips": row.trips, "avg_fare": round(float(row.avg_fare), 2) if row.avg_fare else None}
        for row in result.all()
    ]


@router.get("/by-zone")
async def by_zone(
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Per-pickup-zone aggregates keyed by location_id."""
    stmt = select(
        TaxiZone.location_id,
        TaxiZone.zone,
        func.count(Trip.trip_id).label("trips"),
        func.avg(Trip.fare_amount).label("avg_fare"),
        func.avg(Trip.tip_pct).label("avg_tip_pct"),
    ).join(TaxiZone, Trip.pu_location_id == TaxiZone.location_id)
    
    if start_date:
        stmt = stmt.where(Trip.pickup_datetime >= start_date)
    if end_date:
        stmt = stmt.where(Trip.pickup_datetime < end_date)
    
    stmt = stmt.group_by(TaxiZone.location_id, TaxiZone.zone).order_by(func.count(Trip.trip_id).desc())
    result = await db.execute(stmt)
    return [
        {
            "location_id": row.location_id,
            "zone": row.zone,
            "trips": row.trips,
            "avg_fare": round(float(row.avg_fare), 2) if row.avg_fare else None,
            "avg_tip_pct": round(float(row.avg_tip_pct), 2) if row.avg_tip_pct else None,
        }
        for row in result.all()
    ]


@router.get("/flows")
async def flows(db: AsyncSession = Depends(get_db), top: int = Query(50, le=500)):
    """Top origin to destination pairs for flow analysis."""
    stmt = select(
        Trip.pu_location_id,
        Trip.do_location_id,
        func.count(Trip.trip_id).label("trips"),
    ).where(
        Trip.pu_location_id.isnot(None),
        Trip.do_location_id.isnot(None),
    ).group_by(
        Trip.pu_location_id,
        Trip.do_location_id,
    ).order_by(
        func.count(Trip.trip_id).desc()
    ).limit(top)
    
    result = await db.execute(stmt)
    return [
        {"pu_location_id": row.pu_location_id, "do_location_id": row.do_location_id, "trips": row.trips}
        for row in result.all()
    ]
