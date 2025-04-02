from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str  # Must be either "client" or "host"

class UserResponse(UserBase):
    id: int
    role: str

    class Config:
        orm_mode = True

class UserLogin(UserBase):
    password: str
