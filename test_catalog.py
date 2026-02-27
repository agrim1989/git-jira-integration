import pytest
from fastapi.testclient import TestClient
from catalog import router

client = TestClient(router)

def test_create_book():
    book = {"title": "test", "author": "test"}
    response = client.post("/books", json=book)
    assert response.status_code == 201

def test_read_books():
    response = client.get("/books")
    assert response.status_code == 200

def test_read_book():
    response = client.get("/books/1")
    assert response.status_code == 200

def test_update_book():
    book = {"title": "test2", "author": "test2"}
    response = client.put("/books/1", json=book)
    assert response.status_code == 200

def test_delete_book():
    response = client.delete("/books/1")
    assert response.status_code == 200