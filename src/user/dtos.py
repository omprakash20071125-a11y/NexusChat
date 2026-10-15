from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    username : str
    password : str
    email : EmailStr

class UserResponseSchema(BaseModel):
    id: int
    username : str
    email : EmailStr
    is_online: bool
    last_seen: datetime

class LoginSchema(BaseModel):
    email : str
    password : str
