import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_users():
    response = client.get("/users")
    assert response.status_code == 200

def test_create_user():
    user = {"username": "test", "password": "test", "role": "test"}
    response = client.post("/register", json=user)
    assert response.status_code == 201

def test_login_user():
    user = {"username": "test", "password": "test"}
    response = client.post("/login", json=user)
    assert response.status_code == 200