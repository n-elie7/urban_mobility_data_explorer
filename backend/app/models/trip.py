from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Numeric, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

# trip metadata table
class Trip(Base):
    __tablename__ = "trip"

    trip_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendor.vendor_id"))
    pickup_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    dropoff_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    passenger_count: Mapped[int | None] = mapped_column(SmallInteger)
    trip_distance: Mapped[float | None] = mapped_column(Numeric(8, 2))
    rate_code_id: Mapped[int | None] = mapped_column(ForeignKey("rate_code.rate_code_id"))
    store_and_fwd_flag: Mapped[bool | None] = mapped_column(Boolean)
    pu_location_id: Mapped[int | None] = mapped_column(ForeignKey("taxi_zone.location_id"), index=True)
    do_location_id: Mapped[int | None] = mapped_column(ForeignKey("taxi_zone.location_id"), index=True)
    payment_type_id: Mapped[int | None] = mapped_column(ForeignKey("payment_type.payment_type_id"))
    fare_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    extra: Mapped[float | None] = mapped_column(Numeric(10, 2))
    mta_tax: Mapped[float | None] = mapped_column(Numeric(10, 2))
    tip_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    tolls_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    improvement_surcharge: Mapped[float | None] = mapped_column(Numeric(10, 2))
    total_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    congestion_surcharge: Mapped[float | None] = mapped_column(Numeric(10, 2))

    trip_duration_sec: Mapped[int | None] = mapped_column(BigInteger)
    avg_speed_mph: Mapped[float | None] = mapped_column(Numeric(6, 2))
    fare_per_mile: Mapped[float | None] = mapped_column(Numeric(10, 2))
    tip_pct: Mapped[float | None] = mapped_column(Numeric(6, 2))
    pickup_hour: Mapped[int | None] = mapped_column(SmallInteger, index=True)
    pickup_dow: Mapped[int | None] = mapped_column(SmallInteger)
    is_weekend: Mapped[bool | None] = mapped_column(Boolean)
    is_inter_borough: Mapped[bool | None] = mapped_column(Boolean)

    __table_args__ = (
        Index("ix_trip_pickup_dt", "pickup_datetime"),
        Index("ix_trip_pu_do", "pu_location_id", "do_location_id"),
    )
