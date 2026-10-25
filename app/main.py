import datetime
from .utils import haversine_km
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import models, schemas

Base.metadata.create_all(bind=engine)
app = FastAPI(title="GramSetu API")


@app.get("/")
def home():
    return {"message": "Welcome to GramSetu"}


@app.get("/storages")
def list_storages(db: Session = Depends(get_db)):
    storages = db.scalars(select(models.Storage)).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "district": s.district,
            "capacity_qtl": s.capacity_qtl,
            "price_per_qtl_week": s.price_per_qtl_week,
            "temperature_c": s.temperature_c,
        }
        for s in storages
    ]


@app.post("/farmers", status_code=201)
def create_farmer(data: schemas.FarmerCreate, db: Session = Depends(get_db)):
    farmer = models.Farmer(**data.model_dump())
    db.add(farmer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Phone number already registered")
    db.refresh(farmer)
    return {"id": farmer.id, "name": farmer.name, "village": farmer.village}


@app.post("/bookings", status_code=201)
def create_booking(data: schemas.BookingCreate, db: Session = Depends(get_db)):
    farmer = db.get(models.Farmer, data.farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    storage = db.get(models.Storage, data.storage_id)
    if storage is None:
        raise HTTPException(status_code=404, detail="Storage not found")

    new_start = data.start_date
    new_end = new_start + datetime.timedelta(weeks=data.weeks)

    # Add up quintals already booked at this storage during overlapping dates
    existing = db.scalars(
        select(models.Booking).where(models.Booking.storage_id == storage.id)
    ).all()
    booked = 0
    for b in existing:
        b_end = b.start_date + datetime.timedelta(weeks=b.weeks)
        if b.start_date < new_end and b_end > new_start:
            booked += b.quantity_qtl

    free = storage.capacity_qtl - booked
    if data.quantity_qtl > free:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough space. Only {free} quintals free for those dates.",
        )

    total_cost = data.quantity_qtl * data.weeks * storage.price_per_qtl_week
    booking = models.Booking(**data.model_dump(), total_cost=total_cost)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {
        "booking_id": booking.id,
        "storage": storage.name,
        "quantity_qtl": booking.quantity_qtl,
        "weeks": booking.weeks,
        "total_cost": booking.total_cost,
        "free_after_booking": free - data.quantity_qtl,
    }
@app.get("/storages/nearby")
def nearby_storages(
    lat: float,
    lon: float,
    radius_km: float = 50,
    db: Session = Depends(get_db),
):
    storages = db.scalars(select(models.Storage)).all()
    results = []
    for s in storages:
        distance = haversine_km(lat, lon, s.latitude, s.longitude)
        if distance <= radius_km:
            results.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "district": s.district,
                    "distance_km": round(distance, 1),
                    "price_per_qtl_week": s.price_per_qtl_week,
                    "temperature_c": s.temperature_c,
                }
            )
    results.sort(key=lambda r: r["distance_km"])
    return results