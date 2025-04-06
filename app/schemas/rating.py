from pydantic import BaseModel

class RatingCreate(BaseModel):
    restaurant_id: int
    score: int

    class Config:
        orm_mode = True

class RatingResponse(RatingCreate):
    id: int
    user_id: int
