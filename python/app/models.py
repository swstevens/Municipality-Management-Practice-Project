# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    TECHNICIAN = "technician"
    OPERATOR = "operator"
    ADMIN = "admin"

class AlertStatus(str, enum.Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", backref="customer_profile")

class WaterQualityReading(Base):
    __tablename__ = "water_quality_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    location = Column(String(100), nullable=True, index=True)
    ph_level = Column(Numeric(3, 2), nullable=False)
    chlorine_level = Column(Numeric(4, 2), nullable=False)
    turbidity = Column(Numeric(5, 2), nullable=True)
    temperature = Column(Numeric(4, 1), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def get_alert_status(self) -> AlertStatus:
        """Calculate alert status based on readings"""
        if self.ph_level < 6.5 or self.ph_level > 8.5:
            return AlertStatus.CRITICAL
        elif self.chlorine_level < 0.2:
            return AlertStatus.WARNING
        return AlertStatus.NORMAL

class InfrastructureAsset(Base):
    __tablename__ = "infrastructure_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String(20), nullable=False)  # pipeline, pump, valve, meter
    asset_id = Column(String(50), unique=True, index=True, nullable=False)
    location = Column(String(100), nullable=True)
    installation_date = Column(DateTime(timezone=True), nullable=True)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")  # active, maintenance, offline
    created_at = Column(DateTime(timezone=True), server_default=func.now())