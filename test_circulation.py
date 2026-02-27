import pytest
from fastapi.testclient import TestClient
from circulation import router

client = TestClient(router)

def test_create_loan():
    loan = {"user_id": 1, "book_id": 1}
    response = client.post("/loans", json=loan)
    assert response.status_code == 201

def test_read_loans():
    response = client.get("/loans")
    assert response.status_code == 200

def test_read_loan():
    response = client.get("/loans/1")
    assert response.status_code == 200

def test_update_loan():
    loan = {"user_id": 2, "book_id": 2}
    response = client.put("/loans/1", json=loan)
    assert response.status_code == 200

def test_delete_loan():
    response = client.delete("/loans/1")
    assert response.status_code == 200