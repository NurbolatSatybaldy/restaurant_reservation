from pydantic import BaseModel

class RestaurantBase(BaseModel):
    name: str
    num_tables: int
    table_capacity: int
    working_time: str

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantResponse(RestaurantBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
