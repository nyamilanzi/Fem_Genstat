"""
User models for authentication
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Email validation - using str for now, can add email-validator later
EmailStr = str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

