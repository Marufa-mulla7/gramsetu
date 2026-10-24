import datetime
from sqlalchemy import String, Float, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Farmer(Base):
    __tablename__ = "farmers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(15), unique=True)
    village: Mapped[str] = mapped_column(String(100))

class Storage(Base):
    __tablename__ = "storages"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    district: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    capacity_qtl: Mapped[int]
    price_per_qtl_week: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float] = mapped_column(Float)

class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"))
    storage_id: Mapped[int] = mapped_column(ForeignKey("storages.id"))
    crop: Mapped[str] = mapped_column(String(50))
    quantity_qtl: Mapped[int]
    start_date: Mapped[datetime.date] = mapped_column(Date)
    weeks: Mapped[int]
    total_cost: Mapped[float] = mapped_column(Float)