from sqlalchemy import Column, Integer, DateTime, ForeignKey
from app.db.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    table_number = Column(Integer, nullable=False)  # New field: specific table number
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
