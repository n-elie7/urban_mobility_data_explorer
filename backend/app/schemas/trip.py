from datetime import datetime
from pydantic import BaseModel

# Full trip detail  used when returning a single trip or detailed records
class TripResponse(BaseModel):
    trip_id: int
    pickup_datetime: datetime
    dropoff_datetime: datetime
    trip_distance: float | None
    pu_location_id: int | None
    do_location_id: int | None
    fare_amount: float | None
    tip_amount: float | None
    total_amount: float | None
    avg_speed_mph: float | None

    model_config = {"from_attributes": True}

# Query params the frontend can send to filter/sort trips.
# All fields optional the user picks whichever filters they want.
class TripFilterParams(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    min_distance: float | None = None
    max_distance: float | None = None
    borough: str | None = None
    payment_type_id: int | None = None
    limit: int = 100
    offset: int = 0
