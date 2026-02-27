import pytest
from fastapi.testclient import TestClient
from search import router

client = TestClient(router)

def test_search():
    query = {"query": "test"}
    response = client.get("/search", json=query)
    assert response.status_code == 200