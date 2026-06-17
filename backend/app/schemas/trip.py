from datetime import datetime
from pydantic import BaseModel


# Full trip detail  used when returning a single trip or detailed records
class TripResponse(BaseModel):
    trip_id: int
    vendor_id: int | None
    pickup_datetime: datetime
    dropoff_datetime: datetime
    passenger_count: int | None
    trip_distance: float | None
    rate_code_id: int | None
    store_and_fwd_flag: bool | None
    pu_location_id: int | None
    do_location_id: int | None
    payment_type_id: int | None
    fare_amount: float | None
    extra: float | None
    mta_tax: float | None
    tip_amount: float | None
    tolls_amount: float | None
    improvement_surcharge: float | None
    total_amount: float | None
    congestion_surcharge: float | None

    # derived / feature engineered fields
    trip_duration_sec: int | None
    fare_per_mile: float | None
    tip_pct: float | None
    pickup_hour: int | None
    pickup_dow: int | None
    is_weekend: bool | None
    is_inter_borough: bool | None

    model_config = {"from_attributes": True}
# A lightweight version used for dashboard tables and lists.
# Only includes the fields needed to display each row, reducing unnecessary data transfer.
class TripSummary(BaseModel):
    trip_id: int
    pickup_datetime: datetime
    dropoff_datetime: datetime
    trip_distance: float | None
    pu_location_id: int | None
    do_location_id: int | None
    fare_amount: float | None
    total_amount: float | None
    tip_pct: float | None

    model_config = {"from_attributes": True}
# Query params the frontend can send to filter/sort trips.
# All fields optional the user picks whichever filters they want.
class TripFilterParams(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    pu_location_id: int | None = None
    do_location_id: int | None = None
    min_distance: float | None = None
    max_distance: float | None = None
    min_fare: float | None = None
    max_fare: float | None = None
    is_weekend: bool | None = None
    payment_type_id: int | None = None

    sort_by: str = "pickup_datetime"
    sort_order: str = "desc"

    page: int = 1
    page_size: int = 50
