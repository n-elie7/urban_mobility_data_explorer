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
        FROfrom fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.session import get_db
from app.core.algorithms import top_k

from app.models.trip import Trip

router = APIRouter()

@router.get("/summary")
async def summary(database: AsyncSession = Depends(get_db)):
    statement = select(
        func.count(Trip.trip_id).label("total_trips"),
        func.avg(Trip.fare_amount).label("average_fare"),
        func.avg(Trip.trip_distance).label("average_distance"),
    )
    result = await database.execute(statement)
    row = result.one()
    return {
        "total_trips": row.total_trips,
        "average_fare": round(float(row.average_fare), 2) if row.average_fare else None,
        "average_distance": round(float(row.average_distance), 2) if row.average_distance else None,
    }

def _window(start_date: datetime | None, end_date: datetime | None):
    clauses, parameters = [], {}
    if start_date:
        clauses.append("pickup_datetime >= :start_date")
        parameters["start_date"] = start_date
    if end_date:
        clauses.append("pickup_datetime < :end_date")
        parameters["end_date"] = end_date
    where_clause = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where_clause, parameters


@router.get("/hourly-demand")
async def hourly_demand(database: AsyncSession = Depends(get_db),
                        start_date: datetime | None = None, end_date: datetime | None = None):
    where_clause, parameters = _window(start_date, end_date)
    statement = text(f"""
        SELECT pickup_hour,
               COUNT(*) AS trips,
               AVG(fare_amount)::float AS average_fare,
               AVG(tip_pct)::float AS average_tip_percent
        FROM trip {where_clause}
        GROUP BY pickup_hour ORDER BY pickup_hour
    """)
    rows = (await database.execute(statement, parameters)).mappings().all()
    return [dict(row) for row in rows]


@router.get("/by-zone")
async def by_zone(database: AsyncSession = Depends(get_db),
                  start_date: datetime | None = None, end_date: datetime | None = None,
                  top: int | None = None):
    """Per-pickup-zone aggregates keyed by location_id.

    When `top` is given, the K zones with the highest trip count are
    selected using the custom Min-Heap Top-K in `app.core.algorithms`
    (O(n log k)). When `top` is omitted, every zone is returned so the
    choropleth has data for all polygons.
    """
    where_clause, parameters = _window(start_date, end_date)
    statement = text(f"""
        SELECT z.location_id, z.zone, b.name AS borough,
               COUNT(*) AS trips,
               AVG(t.fare_amount)::float AS average_fare,
               AVG(t.tip_pct)::float AS average_tip_percent
        FROM trip t
        JOIN taxi_zone z ON z.location_id = t.pu_location_id
        LEFT JOIN borough b ON b.borough_id = z.borough_id
        {where_clause}
        GROUP BY z.location_id, z.zone, b.name
    """)
    rows = [dict(row) for row in (await database.execute(statement, parameters)).mappings().all()]
    if top is not None and top > 0:
        return top_k(rows, k=top, key=lambda row: row["trips"] or 0)
    rows.sort(key=lambda row: row["trips"] or 0, reverse=True)
    return rows


@router.get("/flows")
async def flows(database: AsyncSession = Depends(get_db), top: int = 50):
    """Top origin->destination pairs enriched with zone centroids.

    Pulls every distinct OD pair aggregate (with the pickup and dropoff
    zone centroid coordinates) from Postgres without SQL ORDER BY /
    LIMIT, then keeps the K largest using the custom Min-Heap Top-K
    from `app.core.algorithms` (O(n log k)).
    """
    statement = text("""
        WITH origin_destination AS (
          SELECT pu_location_id, do_location_id, COUNT(*) AS trips
          FROM trip
          WHERE pu_location_id IS NOT NULL AND do_location_id IS NOT NULL
          GROUP BY pu_location_id, do_location_id
        )
        SELECT origin_destination.pu_location_id,
               origin_destination.do_location_id,
               origin_destination.trips,
               ST_Y(ST_Centroid(pickup_zone.geom))::float AS pickup_latitude,
               ST_X(ST_Centroid(pickup_zone.geom))::float AS pickup_longitude,
               ST_Y(ST_Centroid(dropoff_zone.geom))::float AS dropoff_latitude,
               ST_X(ST_Centroid(dropoff_zone.geom))::float AS dropoff_longitude
        FROM origin_destination
        JOIN taxi_zone pickup_zone ON pickup_zone.location_id = origin_destination.pu_location_id
        JOIN taxi_zone dropoff_zone ON dropoff_zone.location_id = origin_destination.do_location_id
        WHERE pickup_zone.geom IS NOT NULL AND dropoff_zone.geom IS NOT NULL
    """)
    rows = [dict(row) for row in (await database.execute(statement)).mappings().all()]
    return top_k(rows, k=top, key=lambda row: row["trips"] or 0)


@router.get("/data-range")
async def data_range(database: AsyncSession = Depends(get_db)):
    """Earliest and latest pickup_datetime in the loaded data.

    Used by the frontend to build "Full range / First day / First week"
    presets without hard-coding a calendar window.
    """
    statement = text("SELECT MIN(pickup_datetime) AS start, MAX(pickup_datetime) AS end FROM trip")
    row = (await database.execute(statement)).mappings().one()
    return {
        "start": row["start"].isoformat() if row["start"] else None,
        "end": row["end"].isoformat() if row["end"] else None,
    }M trip
        WHERE pu_location_id IS NOT NULL AND do_location_id IS NOT NULL
        GROUP BY pu_location_id, do_location_id
        ORDER BY trips DESC LIMIT :top
    """)
    rows = (await db.execute(sql, {"top": top})).mappings().all()
    return [dict(r) for r in rows]
