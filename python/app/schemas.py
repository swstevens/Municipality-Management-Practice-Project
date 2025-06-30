# app/schemas.py
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from models import UserRole, AlertStatus

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.CUSTOMER

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    model_config = {"from_attributes": True}

# Water Quality Reading schemas
class WaterQualityReadingBase(BaseModel):
    sensor_id: str
    location: Optional[str] = None
    ph_level: Decimal
    chlorine_level: Decimal
    turbidity: Optional[Decimal] = None
    temperature: Optional[Decimal] = None
    timestamp: datetime
    
    @field_validator('ph_level')
    @classmethod
    def validate_ph_level(cls, v):
        if v < 0 or v > 14:
            raise ValueError('pH level must be between 0 and 14')
        return v
    
    @field_validator('chlorine_level')
    @classmethod
    def validate_chlorine_level(cls, v):
        if v < 0:
            raise ValueError('Chlorine level cannot be negative')
        return v

class WaterQualityReadingCreate(WaterQualityReadingBase):
    pass

class WaterQualityReadingResponse(WaterQualityReadingBase):
    id: int
    created_at: datetime
    alert_status: AlertStatus
    
    model_config = {"from_attributes": True}

# Customer schemas
class CustomerBase(BaseModel):
    account_number: str
    name: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

class DashboardData(BaseModel):
    total_readings: int
    alert_count: int
    avg_ph_level: float
    avg_chlorine_level: float
    recent_alerts: List[WaterQualityReadingResponse]
    sensor_count: int
    last_updated: datetime