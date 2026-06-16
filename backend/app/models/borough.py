from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class Borough(Base):
    __tablename__ = "borough"

    borough_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, index=True)

    zones: Mapped[list["TaxiZone"]] = relationship(back_populates="borough")  # noqa: F821
