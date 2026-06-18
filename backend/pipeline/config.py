from pathlib import Path
from app.core.config import get_settings

settings = get_settings()

# data source paths
DATA = Path("/data")
RAW = DATA / "raw"
PROCESSED = DATA / "processed"

ZONES_SHP = RAW / "taxi_zones" / "taxi_zones.shp"
LOOKUP_CSV = RAW / "taxi_zone_lookup.csv"
TRIPS_GLOB = "yellow_tripdata_*.parquet"

# cleaning thresholds gauge
MAX_TRIP_DISTANCE_MI = 100
MAX_SPEED_MPH = 80
MIN_DURATION_SEC = 30
MAX_DURATION_SEC = 6 * 3600
MAX_FARE = 1000
MAX_TIP_PCT = 100
SRID_SOURCE = 2263
SRID_TARGET = 4326
