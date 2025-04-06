from pydantic import BaseModel
from datetime import datetime

class ReservationBase(BaseModel):
    restaurant_id: int
    table_number: int
    start_time: datetime
    end_time: datetime

class ReservationCreate(ReservationBase):
    pass

class ReservationResponse(ReservationBase):
    id: int
    client_id: int

    class Config:
        from_attributes = True
