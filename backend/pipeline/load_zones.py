import logging
import geopandas as gpd
from shapely.geometry import MultiPolygon
from sqlalchemy import create_engine, text

from pipeline import config as C

log = logging.getLogger("pipeline.zones")


def _as_multipolygon(geom):
    return geom if geom.geom_type == "MultiPolygon" else MultiPolygon([geom])

# load the taxi_zones shapefile into PostGIS as the spatial dimension.
def run() -> None:
    logging.basicConfig(level="INFO")
    geo_dataframe = gpd.read_file(C.ZONES_SHP)
    log.info("read %d raw polygon records (crs=%s)", len(geo_dataframe), geo_dataframe.crs)

    geo_dataframe = geo_dataframe.to_crs(epsg=C.SRID_TARGET)

    geo_dataframe = (
        geo_dataframe.dissolve(by="LocationID", aggfunc="first")
        .reset_index()
        .rename(columns={"LocationID": "location_id", "zone": "zone", "borough": "borough_name"})
    )
    
    geo_dataframe["geom"] = geo_dataframe.geometry.apply(_as_multipolygon)
    geo_dataframe = geo_dataframe.set_geometry("geom")[["location_id", "zone", "borough_name", "geom"]]
    log.info("dissolved to %d unique zones", len(geo_dataframe))

    engine = create_engine(C.settings.sync_db_url)

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        
        boroughs = sorted(geo_dataframe["borough_name"].dropna().unique())
        for borough in boroughs:
            connection.execute(text(
                "INSERT INTO borough (name) VALUES (:n) ON CONFLICT (name) DO NOTHING"
            ), {"n": borough})

        rows = connection.execute(text("SELECT borough_id, name FROM borough")).fetchall()
        bmap = {name: bid for bid, name in rows}

        geo_dataframe["borough_id"] = geo_dataframe["borough_name"].map(bmap)

    output = geo_dataframe[["location_id", "zone", "borough_id", "geom"]].set_geometry("geom")
    output.to_postgis("taxi_zone", engine, if_exists="append", index=False)
    log.info("loaded %d zones into taxi_zone", len(output))


if __name__ == "__main__":
    run()