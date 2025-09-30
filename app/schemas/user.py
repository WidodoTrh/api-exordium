from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True
