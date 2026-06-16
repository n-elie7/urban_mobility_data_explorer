from pydantic import BaseModel


# What we return when someone reads a taxi zone
class ZoneResponse(BaseModel):
    location_id: int
    zone: str | None
    service_zone: str | None
    borough_id: int | None

    model_config = {"from_attributes": True}
