from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid
import re


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User registration model"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class User(UserBase):
    """User model returned from API"""
    id: str
    role: Literal["admin", "user"] = "user"
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    usage_quota: int = 100000  # tokens per day
    usage_today: int = 0
    total_usage: int = 0

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password (internal use)"""
    hashed_password: str


class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    email: str
    role: str
    exp: datetime


class APIKey(BaseModel):
    """API Key model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    key: str  # hashed
    prefix: str  # first 8 chars for identification
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    """API Key creation model"""
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    """API Key response (only returned once on creation)"""
    id: str
    name: str
    key: str  # Full key - only shown once
    prefix: str
    created_at: datetime


class UsageStats(BaseModel):
    """User usage statistics"""
    user_id: str
    tokens_used_today: int
    tokens_quota: int
    total_tokens_used: int
    requests_today: int
    cost_today: float
    cost_total: float
