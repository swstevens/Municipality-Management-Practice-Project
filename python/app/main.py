from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import os

# Change relative imports to absolute imports
import models
import schemas
import crud
import auth
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Water Utility Management API",
    description="A comprehensive water utility management system",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Mount static files (for any additional static assets)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Water Utility Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Dashboard HTML page
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the water utility dashboard HTML page"""
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard not found</h1><p>Please create dashboard.html file</p>", 
            status_code=404
        )
# Authentication endpoints
@app.post("/auth/register", response_model=schemas.UserResponse)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    return crud.create_user(db=db, user=user)

@app.post("/auth/login", response_model=schemas.Token)
def login(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

# Water Quality Reading endpoints
@app.get("/api/v1/water-quality", response_model=List[schemas.WaterQualityReadingResponse])
def get_water_quality_readings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location: Optional[str] = Query(None),
    sensor_id: Optional[str] = Query(None),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    readings = crud.get_water_quality_readings(
        db, skip=skip, limit=limit, location=location, sensor_id=sensor_id
    )
    
    # Add alert_status to response
    for reading in readings:
        reading.alert_status = reading.get_alert_status()
    
    return readings

@app.post("/api/v1/water-quality", response_model=schemas.WaterQualityReadingResponse)
def create_water_quality_reading(
    reading: schemas.WaterQualityReadingCreate,
    current_user: models.User = Depends(auth.require_operator_or_admin),
    db: Session = Depends(get_db)
):
    db_reading = crud.create_water_quality_reading(db=db, reading=reading)
    db_reading.alert_status = db_reading.get_alert_status()
    
    # Log alert if necessary
    if db_reading.get_alert_status() != models.AlertStatus.NORMAL:
        print(f"🚨 WATER QUALITY ALERT: {db_reading.get_alert_status()} "
              f"- Sensor {db_reading.sensor_id} at {db_reading.location}")
    
    return db_reading

@app.get("/api/v1/water-quality/dashboard", response_model=schemas.DashboardData)
def get_dashboard_data(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.get_dashboard_stats(db)

@app.get("/api/v1/water-quality/alerts", response_model=List[schemas.WaterQualityReadingResponse])
def get_alert_readings(
    current_user: models.User = Depends(auth.require_operator_or_admin),
    db: Session = Depends(get_db)
):
    alerts = crud.get_alert_readings(db)
    for alert in alerts:
        alert.alert_status = alert.get_alert_status()
    return alerts

# Customer endpoints
@app.get("/api/v1/customers", response_model=List[schemas.CustomerResponse])
def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.get_customers(db, skip=skip, limit=limit)

@app.post("/api/v1/customers", response_model=schemas.CustomerResponse)
def create_customer(
    customer: schemas.CustomerCreate,
    current_user: models.User = Depends(auth.require_operator_or_admin),
    db: Session = Depends(get_db)
):
    return crud.create_customer(db=db, customer=customer)

# User management endpoints
@app.get("/api/v1/users/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)