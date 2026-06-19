import logging
import pandas as pd
from sqlalchemy import create_engine, text
from pipeline import config as C
from pipeline.clean_trips import clean
from pipeline.transparency_log import TransparencyLog

log = logging.getLogger("pipeline.trips")


# bulk insert via PostgreSQL COPY (no 65k bind-parameter limit).
def _psql_insert_copy(table, conn, keys, data_iter):
    import csv
    from io import StringIO

    def fix(v):
        if pd.isna(v):
            return None
        if isinstance(v, float) and v.is_integer():
            return int(v)
        return v

    database_api_connection = conn.connection
    with database_api_connection.cursor() as cursor:
        buffer = StringIO()
        writer = csv.writer(buffer)

        for row in data_iter:
            writer.writerow([fix(v) for v in row])

        buffer.seek(0)
        cols = ", ".join(f'"{k}"' for k in keys)
        name = f"{table.schema}.{table.name}" if table.schema else table.name

        cursor.copy_expert(f"COPY {name} ({cols}) FROM STDIN WITH CSV", buffer)


def _iter_chunks(path, batch_size):
    """Yield the file in memory-friendly pieces: row-groups for parquet,
    line-count chunks for csv."""
    if path.suffix == ".parquet":
        import pyarrow.parquet as pq
        for batch in pq.ParquetFile(path).iter_batches(batch_size=batch_size):
            yield batch.to_pandas()
    else:
        yield from pd.read_csv(path, chunksize=batch_size)

KEEP = [
    "vendor_id", "pickup_datetime", "dropoff_datetime", "passenger_count",
    "trip_distance", "rate_code_id", "store_and_fwd_flag", "pu_location_id",
    "do_location_id", "payment_type_id", "fare_amount", "extra", "mta_tax",
    "tip_amount", "tolls_amount", "improvement_surcharge", "total_amount",
    "congestion_surcharge", "trip_duration_sec", "avg_speed_mph",
    "fare_per_mile", "tip_pct", "pickup_hour", "pickup_dow", "is_weekend",
    "is_inter_borough",
]


def _borough_map(engine) -> dict[int, str]:
    with engine.connect() as c:
        rows = c.execute(text("""
            SELECT z.location_id, b.name FROM taxi_zone z
            LEFT JOIN borough b ON b.borough_id = z.borough_id
        """)).fetchall()
    return {location_id: name for location_id, name in rows}


def run() -> None:
    logging.basicConfig(level="INFO")
    engine = create_engine(C.settings.sync_db_url)
    borough_map = _borough_map(engine)
    transparency_log = TransparencyLog()
    batch = C.settings.trip_batch_size

    files = sorted(C.RAW.glob(C.TRIPS_GLOB)) or sorted(C.RAW.glob("yellow_tripdata_*.csv"))

    for path in files:
        log.info("ingesting %s", path.name)
        for i, chunk in enumerate(_iter_chunks(path, batch)):
            cleaned = clean(chunk, borough_map, transparency_log).reindex(columns=KEEP)
            cleaned.to_sql("trip", engine, if_exists="append", index=False,
                           method=_psql_insert_copy)
            log.info("  %s chunk %d done (running rows_out=%d)", path.name, i, transparency_log.total_out)

    transparency_log.write_csv(C.PROCESSED / "transparency_log.csv")
    log.info("ingestion summary: %s", transparency_log.summary())


if __name__ == "__main__":
    run()