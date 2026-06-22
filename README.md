#  TaxiPulse Dashboard

An end-to-end stack for exploring NYC Yellow Taxi trip records. Raw TLC
files are cleaned and bulk-loaded into PostGIS, a FastAPI service exposes
aggregate analytics, and a Leaflet + Chart.js dashboard renders the
results as a choropleth and supporting charts.

---

## Architecture

Three containers orchestrated by `docker-compose.yml`:

| Service     | Container   | Image / Build              | Host port | Purpose                                                     |
| ----------- | ----------- | -------------------------- | --------- | ----------------------------------------------------------- |
| `db`        | `taxi_db`   | `postgis/postgis:16-3.4`   | `5433`    | Postgres 16 with the PostGIS 3.4 extension                  |
| `backend`   | `taxi_api`  | `backend/Dockerfile`       | `8000`    | FastAPI + SQLAlchemy (async asyncpg, sync psycopg2 for ETL) |
| `frontend`  | `taxi_web`  | `nginx:1.27-alpine`        | `8081`    | Serves the static dashboard and proxies `/api/` to backend  |

Data flows: raw files in `data/raw/` → pipeline scripts → PostGIS →
FastAPI → nginx → browser.

---

## Tech stack

- **Database** — PostgreSQL 16 with PostGIS 3.4 for spatial joins.
- **Backend** — FastAPI, SQLAlchemy 2.x (async + sync engines), Pydantic
  settings, pandas / geopandas / shapely for ETL, psycopg2 `COPY` for
  bulk inserts.
- **Frontend** — Plain HTML/CSS/JS, Leaflet 1.9 for the map, Chart.js
  4.4 for bar charts. Same-origin via nginx, no build step.
- **Custom DSA** — Hand-written binary Min-Heap and Top-K in
  `backend/app/core/algorithms.py`, used by the `/api/analytics/flows`
  and `/api/analytics/by-zone?top=K` endpoints. Pseudo-code and
  complexity analysis live in the module docstring.

---

## Project layout

```
urban/
  data/
    raw/                          <- DROP RAW DATA HERE (see below)
      taxi_zones/                 <- shapefile bundle (.shp, .shx, .dbf, .prj, ...)
      taxi_zone_lookup.csv
      yellow_tripdata_YYYY-MM.csv | .parquet
    processed/
      transparency_log.csv        <- written by load_trips
  backend/
    Dockerfile
    requirements.txt
    app/
      main.py                     <- FastAPI entry point
      api/routes/                 <- analytics.py, health.py, trip.py, zones.py
      core/
        config.py                 <- pydantic settings (.env driven)
        algorithms.py             <- custom MinHeap + top_k (DSA)
        logging.py
      database/                   <- async engine + session
      models/                     <- SQLAlchemy ORM (Trip, TaxiZone, Borough, ...)
      schemas/                    <- pydantic response models
    pipeline/
      run_pipeline.py             <- orchestrator (zones -> lookup -> trips)
      seed_dims.py                <- creates schema + seeds vendor/rate_code/payment_type
      load_zones.py               <- shapefile -> taxi_zone
      load_lookup.py              <- CSV lookup -> taxi_zone rows without geom
      load_trips.py               <- chunked clean + COPY into trip
      clean_trips.py              <- validation + derived columns
      transparency_log.py         <- tracks dropped / nulled records
      config.py                   <- paths and thresholds
  frontend/
    index.html
    styles.css
    nginx.conf
    js/
      api.js                      <- thin fetch wrappers
      app.js                      <- wiring, filters, refresh
      map.js                      <- Leaflet choropleth + legend
      charts.js                   <- Chart.js bar charts
  docker-compose.yml
  Makefile                        <- shortcuts for stack + pipeline commands
  .env.example
```

---

## Prerequisites

- Docker Engine 24+ with the Compose plugin (`docker compose` v2).
- ~5 GB free disk for the `pgdata` volume after loading a single TLC month.
- ~2 GB RAM headroom for the backend during trip ingestion (chunked, so
  you can lower `TRIP_BATCH_SIZE` in `.env` if your machine is tight).

No Python install is required on the host — every command runs inside
the backend container.

---

## Where to put the raw data

All raw inputs go under `data/raw/`. The pipeline expects three things:

### 1. Taxi zone shapefile — `data/raw/taxi_zones/`

Download "NYC Taxi Zones" from the TLC site (a `.zip` shapefile bundle).
Unpack the contents so the directory contains at least:

```
data/raw/taxi_zones/taxi_zones.shp
data/raw/taxi_zones/taxi_zones.shx
data/raw/taxi_zones/taxi_zones.dbf
data/raw/taxi_zones/taxi_zones.prj
```

The path is fixed in `backend/pipeline/config.py` as
`ZONES_SHP = RAW / "taxi_zones" / "taxi_zones.shp"`.

### 2. Taxi zone lookup — `data/raw/taxi_zone_lookup.csv`

The companion CSV from the same TLC page. It maps `LocationID -> zone`,
borough, and service zone, including rows that have no polygon. Path:
`LOOKUP_CSV = RAW / "taxi_zone_lookup.csv"`.

### 3. Trip records — `data/raw/yellow_tripdata_YYYY-MM.{parquet,csv}`

Drop one or more monthly TLC Yellow Taxi files directly into
`data/raw/`. Parquet is preferred (smaller, faster); CSV works too. The
loader picks them up via this glob, parquet first:

```
yellow_tripdata_*.parquet
yellow_tripdata_*.csv
```

You can ingest a single month to start (~7.5 M rows, ~10 minutes) and
drop more files in later — re-running the trips loader appends, it does
not truncate.

---

## One-time setup

```bash
git clone <this-repo> urban
cd urban
cp .env.example .env
```

Open `.env` and confirm:

```
POSTGRES_USER=taxi
POSTGRES_PASSWORD=taxi
POSTGRES_DB=taxi
POSTGRES_HOST=db                 # service name inside the compose network
POSTGRES_PORT=5432

CORS_ORIGINS=http://localhost:8080,http://localhost:8081

TRIP_BATCH_SIZE=50000            # lower this if memory is tight
```

The defaults work for a local Docker run. Put your raw files in
`data/raw/` as described above.

---

## Run the stack

```bash
make up        # docker compose up --build -d
make logs      # tail backend logs
```

What comes up:

- `taxi_db` on `localhost:5433` (Postgres + PostGIS).
- `taxi_api` on `http://localhost:8000` (FastAPI docs at `/docs`).
- `taxi_web` on `http://localhost:8081` (the dashboard).

The backend image bind-mounts `./backend` and runs uvicorn with
`--reload`, so code edits restart it automatically.

Quick health check:

```bash
curl http://localhost:8000/health
# {"status":"ok","database":true,"postgis":"3.4.x"}
```

---

## Run the pipeline

The pipeline is split into four idempotent steps. Run them in order the
first time; re-running any step is safe.

```bash
make pipeline-seed      # 1) create schema + seed vendor/rate_code/payment_type
make pipeline-zones     # 2) load taxi_zones shapefile into PostGIS
make pipeline-lookup    # 3) merge taxi_zone_lookup.csv into taxi_zone
make pipeline-trips     # 4) clean + bulk-COPY trip records
```

Or run all four in sequence:

```bash
make pipeline-all       # python -m pipeline.run_pipeline
```

Notes on each step:

- **seed** — `pipeline/seed_dims.py` ensures the PostGIS extension is
  enabled, calls `Base.metadata.create_all(...)` to create every table
  declared in `backend/app/models/`, then seeds the small static
  dimension tables.
- **zones** — Reads the shapefile, reprojects from EPSG:2263 to EPSG:4326,
  dissolves duplicate polygons by `LocationID`, populates the `borough`
  table, and writes 260 multipolygons into `taxi_zone`.
- **lookup** — Inserts the rows missing from the shapefile (Newark,
  Unknown, etc.) and updates `service_zone` on existing rows.
- **trips** — Iterates each Yellow Taxi file in `data/raw/` in chunks of
  `TRIP_BATCH_SIZE`, runs `clean_trips.clean(...)` (range + speed +
  duration + tip-percent validation, plus derived columns like
  `pickup_hour`, `is_inter_borough`), bulk-inserts via `COPY`, and writes
  a transparency report to `data/processed/transparency_log.csv`
  describing what was dropped or nulled and why.

The trips step logs progress every chunk. A typical month finishes in
about ten minutes on a laptop and produces a summary line such as:

```
INFO:pipeline.trips:ingestion summary: {
  'rows_in': 7667792, 'rows_out': 7570903, 'rows_dropped': 96889,
  'by_reason': {...}, 'fields_nulled': {...}
}
```

---

## Use the dashboard

Open `http://localhost:8081`.

- **From / To** — `datetime-local` inputs. Pick a range that overlaps
  your ingested files (e.g. for `yellow_tripdata_2019-01`, choose
  `2019-01-01T00:00` to `2019-02-01T00:00`).
- **Metric** — switches the choropleth fill and the bar charts between
  trip volume, average fare, and average tip percent.
- **Apply** — re-fetches `/api/analytics/hourly-demand` and
  `/api/analytics/by-zone` against the selected window.

The map legend on the bottom-right always reflects the active metric and
the dynamic max for the selected window.

---

## API reference

All routes are mounted under `/api/`.

| Method | Path                              | Notes                                                                                   |
| ------ | --------------------------------- | --------------------------------------------------------------------------------------- |
| GET    | `/health`                         | DB + PostGIS sanity check                                                               |
| GET    | `/api/zones/geojson`              | FeatureCollection of all pickup zones                                                   |
| GET    | `/api/analytics/summary`          | Total trips, average fare, average distance                                             |
| GET    | `/api/analytics/hourly-demand`    | Trips / average fare / average tip percent grouped by hour-of-day; accepts `start_date`, `end_date` |
| GET    | `/api/analytics/by-zone`          | Per-zone aggregates; accepts `start_date`, `end_date`, optional `top` (uses custom Top-K) |
| GET    | `/api/analytics/flows`            | Top K origin->destination pairs, K via `?top=` (uses custom Top-K)                      |
| GET    | `/api/trips`                      | Raw trip rows; supports date / distance / pagination filters                            |

Interactive docs: `http://localhost:8000/docs`.

---

## Custom algorithm

`backend/app/core/algorithms.py` implements a bounded binary Min-Heap and
a `top_k(items, k, key)` routine on top of it. It is used by:

- `GET /api/analytics/flows` — every distinct origin->destination pair is
  pulled from Postgres with no `ORDER BY` / `LIMIT`, then the K largest
  are selected in `O(n log k)` time and `O(k)` space.
- `GET /api/analytics/by-zone?top=K` — same idea for top-K pickup zones.

The module docstring contains the full pseudo-code and complexity
analysis (`O(n log k)` time, `O(k)` space, versus `O(n log n)` / `O(n)`
for the naive sort-then-slice baseline).

---

## Common operations

```bash
# tail logs
make logs

# open a psql shell against the running database
docker compose exec db psql -U taxi -d taxi

# stop everything (data preserved in the pgdata volume)
make down

# stop everything AND wipe the database volume
docker compose down -v
```

---

## Troubleshooting

- **`relation "vendor" does not exist`** — the schema was never created.
  Run `make pipeline-seed`. The seed step calls `create_all(...)` and is
  safe to re-run.
- **Charts are empty but the API is up** — either the pipeline has not
  been run, or the date window does not overlap the ingested months.
  Try `curl 'http://localhost:8000/api/analytics/summary'`; if
  `total_trips` is `0`, run `make pipeline-trips`.
- **`taxi_zones.shp` not found** — confirm the shapefile bundle is at
  `data/raw/taxi_zones/taxi_zones.shp` exactly (the `.shx`, `.dbf`, and
  `.prj` siblings must be next to it).
- **CORS errors when calling the API directly from a different origin**
  — add that origin to `CORS_ORIGINS` in `.env` and `make down && make up`.
- **`uvicorn` import error on backend start** — should be fixed; if it
  recurs, confirm `backend/app/main.py` imports routes as
  `from app.api.routes import ...` (no leading `backend.`).

---

## Reset everything

```bash
docker compose down -v       # drop containers + the pgdata volume
rm -rf data/processed/*      # optional: clear transparency log
make up
make pipeline-seed
make pipeline-zones
make pipeline-lookup
make pipeline-trips
```
