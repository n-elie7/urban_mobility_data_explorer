from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Vendor(Base):
    __tablename__ = "vendor"

    vendor_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))


class RateCode(Base):
    __tablename__ = "rate_code"

    rate_code_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(60))


class PaymentType(Base):
    __tablename__ = "payment_type"
    
    payment_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(40))
