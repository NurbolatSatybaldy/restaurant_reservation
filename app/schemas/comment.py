from pydantic import BaseModel
from typing import Optional

class CommentCreate(BaseModel):
    restaurant_id: int
    content: str
    is_host_message: Optional[int] = 0

    class Config:
        orm_mode = True

class CommentResponse(CommentCreate):
    id: int
    user_id: int
