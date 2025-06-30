from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta

import models
import schemas
from auth import get_password_hash, verify_password


# User CRUD
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Water Quality Reading CRUD
def create_water_quality_reading(
    db: Session, 
    reading: schemas.WaterQualityReadingCreate
) -> models.WaterQualityReading:
    db_reading = models.WaterQualityReading(**reading.dict())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading

def get_water_quality_readings(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    location: Optional[str] = None,
    sensor_id: Optional[str] = None
) -> List[models.WaterQualityReading]:
    query = db.query(models.WaterQualityReading)
    
    if location:
        query = query.filter(models.WaterQualityReading.location == location)
    if sensor_id:
        query = query.filter(models.WaterQualityReading.sensor_id == sensor_id)
    
    return query.order_by(desc(models.WaterQualityReading.timestamp))\
                .offset(skip)\
                .limit(limit)\
                .all()

def get_recent_readings(db: Session, hours: int = 24) -> List[models.WaterQualityReading]:
    since = datetime.utcnow() - timedelta(hours=hours)
    return db.query(models.WaterQualityReading)\
             .filter(models.WaterQualityReading.created_at >= since)\
             .order_by(desc(models.WaterQualityReading.timestamp))\
             .all()

def get_alert_readings(db: Session) -> List[models.WaterQualityReading]:
    return db.query(models.WaterQualityReading)\
             .filter(
                 or_(
                     models.WaterQualityReading.ph_level < 6.5,
                     models.WaterQualityReading.ph_level > 8.5,
                     models.WaterQualityReading.chlorine_level < 0.2
                 )
             )\
             .order_by(desc(models.WaterQualityReading.timestamp))\
             .all()

def get_dashboard_stats(db: Session) -> dict:
    recent_readings = get_recent_readings(db)
    alert_readings = get_alert_readings(db)
    
    # Calculate averages
    if recent_readings:
        avg_ph = sum(float(r.ph_level) for r in recent_readings) / len(recent_readings)
        avg_chlorine = sum(float(r.chlorine_level) for r in recent_readings) / len(recent_readings)
    else:
        avg_ph = avg_chlorine = 0.0
    
    # Count unique sensors
    sensor_count = db.query(models.WaterQualityReading.sensor_id)\
                     .distinct()\
                     .count()
    
    return {
        'total_readings': len(recent_readings),
        'alert_count': len(alert_readings),
        'avg_ph_level': round(avg_ph, 2),
        'avg_chlorine_level': round(avg_chlorine, 2),
        'recent_alerts': alert_readings[:10],  # Last 10 alerts
        'sensor_count': sensor_count,
        'last_updated': datetime.utcnow()
    }

# Customer CRUD
def create_customer(db: Session, customer: schemas.CustomerCreate) -> models.Customer:
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Customer]:
    return db.query(models.Customer).offset(skip).limit(limit).all()