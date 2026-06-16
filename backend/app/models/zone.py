from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class TaxiZone(Base):
    __tablename__ = "taxi_zone"
    
    location_id: Mapped[int] = mapped_column(primary_key=True)

    zone: Mapped[str | None] = mapped_column(String(120))

    service_zone: Mapped[str | None] = mapped_column(String(40), index=True)

    borough_id: Mapped[int | None] = mapped_column(ForeignKey("borough.borough_id"), index=True)

    geom: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True)
    )

    borough: Mapped["Borough | None"] = relationship(back_populates="zones")
