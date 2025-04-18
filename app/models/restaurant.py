from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base
from sqlalchemy.orm import relationship

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    num_tables = Column(Integer, nullable=False)
    table_capacity = Column(Integer, nullable=False)
    working_time = Column(String, nullable=False)

    comments = relationship("Comment", back_populates="restaurant")
    ratings = relationship("Rating", back_populates="restaurant")
