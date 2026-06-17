from pydantic import BaseModel

# zone reponse
class ZoneResponse(BaseModel):
    location_id: int
    zone: str | None
    service_zone: str | None
    borough: str | None

class ZoneGeoJSON(BaseModel):
    """A GeoJSON FeatureCollection ready for Leaflet."""
    type: str = "FeatureCollection"
    features: list[dict]
