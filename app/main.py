from fastapi import FastAPI, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import models

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