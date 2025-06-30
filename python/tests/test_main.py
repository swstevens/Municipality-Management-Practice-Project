# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app import models

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "operator"
    }

@pytest.fixture
def test_reading_data():
    return {
        "sensor_id": "WQ001",
        "location": "Test Plant",
        "ph_level": 7.2,
        "chlorine_level": 0.5,
        "timestamp": "2023-12-01T10:00:00"
    }

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Water Utility Management API" in response.json()["message"]

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user(test_user_data):
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]
    assert "id" in data

def test_login_user(test_user_data):
    # First register the user
    client.post("/auth/register", json=test_user_data)
    
    # Then login
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_water_quality_reading(test_user_data, test_reading_data):
    # Register and login user
    client.post("/auth/register", json=test_user_data)
    login_response = client.post("/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    # Create reading
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/water-quality", json=test_reading_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == test_reading_data["sensor_id"]
    assert data["alert_status"] == "normal"

def test_get_water_quality_readings(test_user_data):
    # Register and login user
    client.post("/auth/register", json=test_user_data)
    login_response = client.post("/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/water-quality", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_dashboard_data(test_user_data):
    # Register and login user
    client.post("/auth/register", json=test_user_data)
    login_response = client.post("/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/water-quality/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_readings" in data
    assert "alert_count" in data

def test_unauthorized_access():
    response = client.get("/api/v1/water-quality")
    assert response.status_code == 401

def test_customer_role_cannot_create_reading():
    # Register customer user
    customer_data = {
        "username": "customer",
        "email": "customer@example.com",
        "password": "password123",
        "role": "customer"
    }
    client.post("/auth/register", json=customer_data)
    
    # Login as customer
    login_response = client.post("/auth/login", json={
        "username": "customer",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # Try to create reading (should fail)
    headers = {"Authorization": f"Bearer {token}"}
    reading_data = {
        "sensor_id": "WQ002",
        "ph_level": 7.0,
        "chlorine_level": 0.3,
        "timestamp": "2023-12-01T10:00:00"
    }
    response = client.post("/api/v1/water-quality", json=reading_data, headers=headers)
    assert response.status_code == 403

# Run tests with: pytest tests/