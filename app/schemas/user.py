from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    google_id: str
    email: str
    name: str

    class Config:
        orm_mode = True
