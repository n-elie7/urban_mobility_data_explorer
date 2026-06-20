import logging
import pandas as pd
from sqlalchemy import create_engine, text
from pipeline import config as C

log = logging.getLogger("pipeline.lookup")

# load taxi_zone_lookup.csv and ensures
# lookup-only ids exist as geom-less zone rows.
def run() -> None:
    logging.basicConfig(level="INFO")
    dataframe = pd.read_csv(C.LOOKUP_CSV)
    dataframe.columns = [c.strip().lower() for c in dataframe.columns]  

    dataframe = dataframe.astype(object).where(pd.notna(dataframe), None)
    engine = create_engine(C.settings.sync_db_url)

    with engine.begin() as connection:
        for _, r in dataframe.iterrows():
            borough = r["borough"]
            bid = None
            if borough is not None:
                connection.execute(text(
                    "INSERT INTO borough (name) VALUES (:b) ON CONFLICT (name) DO NOTHING"
                ), {"b": borough})
                bid = connection.execute(text("SELECT borough_id FROM borough WHERE name=:b"),
                                   {"b": borough}).scalar()
            
            connection.execute(text("""
                INSERT INTO taxi_zone (location_id, zone, service_zone, borough_id)
                VALUES (:lid, :z, :sz, :bid)
                ON CONFLICT (location_id) DO UPDATE
                  SET service_zone = EXCLUDED.service_zone
            """), {"lid": int(r["locationid"]), "z": r["zone"],
                   "sz": r["service_zone"], "bid": bid})
    log.info("processed %d lookup rows", len(dataframe))


if __name__ == "__main__":
    run()