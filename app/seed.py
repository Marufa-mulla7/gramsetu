from .database import Base, engine, SessionLocal
from . import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(models.Storage).count() == 0:
    # DEMO DATA for development only, not real facilities
    db.add_all([
        models.Storage(name="Demo Storage A", district="Mandya", latitude=12.52, longitude=76.90,
                       capacity_qtl=500, price_per_qtl_week=42, temperature_c=4),
        models.Storage(name="Demo Storage B", district="Mandya", latitude=12.55, longitude=76.95,
                       capacity_qtl=300, price_per_qtl_week=38, temperature_c=6),
        models.Storage(name="Demo Storage C", district="Belagavi", latitude=15.85, longitude=74.50,
                       capacity_qtl=800, price_per_qtl_week=45, temperature_c=5),
    ])
    db.commit()
    print("Seeded demo storages")
db.close()