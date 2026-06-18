from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.session import get_db

from app.models.trip import Trip

router = APIRouter()

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

def _window(start_date: datetime | None, end_date: datetime | None):
    clauses, params = [], {}
    if start_date:
        clauses.append("pickup_datetime >= :start_date")
        params["start_date"] = start_date
    if end_date:
        clauses.append("pickup_datetime < :end_date")
        params["end_date"] = end_date
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


@router.get("/hourly-demand")
async def hourly_demand(db: AsyncSession = Depends(get_db),
                        start_date: datetime | None = None, end_date: datetime | None = None):
    where, params = _window(start_date, end_date)
    sql = text(f"""
        SELECT pickup_hour, COUNT(*) AS trips, AVG(fare_amount) AS avg_fare
        FROM trip {where}
        GROUP BY pickup_hour ORDER BY pickup_hour
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/by-zone")
async def by_zone(db: AsyncSession = Depends(get_db),
                  start_date: datetime | None = None, end_date: datetime | None = None):
    """Per-pickup-zone aggregates choropleth values keyed by location_id."""
    where, params = _window(start_date, end_date)
    sql = text(f"""
        SELECT z.location_id, z.zone, b.name AS borough,
               COUNT(*) AS trips, AVG(t.fare_amount) AS avg_fare,
               AVG(t.tip_pct) AS avg_tip_pct
        FROM trip t
        JOIN taxi_zone z ON z.location_id = t.pu_location_id
        LEFT JOIN borough b ON b.borough_id = z.borough_id
        {where}
        GROUP BY z.location_id, z.zone, b.name
        ORDER BY trips DESC
    """)
    rows = (await db.execute(sql, params)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/flows")
async def flows(db: AsyncSession = Depends(get_db), top: int = 50):
    """Top origin to destination pairs for a flow map."""
    sql = text("""
        SELECT pu_location_id, do_location_id, COUNT(*) AS trips
        FROM trip
        WHERE pu_location_id IS NOT NULL AND do_location_id IS NOT NULL
        GROUP BY pu_location_id, do_location_id
        ORDER BY trips DESC LIMIT :top
    """)
    rows = (await db.execute(sql, {"top": top})).mappings().all()
    return [dict(r) for r in rows]
