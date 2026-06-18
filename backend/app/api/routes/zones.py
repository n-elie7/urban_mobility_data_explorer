from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.session import get_db

router = APIRouter()

@router.get("/geojson")
async def zones_geojson(db: AsyncSession = Depends(get_db)):
    sql = text(
        """
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(f), '[]'::json)
        )
        FROM (
          SELECT json_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(z.geom)::json,
            'properties', json_build_object(
                'location_id', z.location_id,
                'zone', z.zone,
                'borough', b.name,
                'service_zone', z.service_zone
            )
          ) AS f
          FROM taxi_zone z
          LEFT JOIN borough b ON b.borough_id = z.borough_id
          WHERE z.geom IS NOT NULL
        ) sub
        """
    )
    response = await db.execute(sql)
    return response.scalar()

