import datetime
from pydantic import BaseModel, Field

class FarmerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=15)
    village: str = Field(min_length=2, max_length=100)

class BookingCreate(BaseModel):
    farmer_id: int
    storage_id: int
    crop: str = Field(min_length=2, max_length=50)
    quantity_qtl: int = Field(gt=0)
    start_date: datetime.date
    weeks: int = Field(ge=1, le=12)