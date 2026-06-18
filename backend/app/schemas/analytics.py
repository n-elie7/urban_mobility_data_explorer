from pydantic import BaseModel

class HourlyDemand(BaseModel):
    pickup_hour: int
    trips: int
    avg_fare: float | None

class ZoneStat(BaseModel):
    location_id: int
    zone: str | None
    borough: str | None
    trips: int
    avg_fare: float | None
    avg_tip_pct: float | None

class FlowEdge(BaseModel):
    pu_location_id: int
    do_location_id: int
    trips: int
