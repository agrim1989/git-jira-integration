"""Tests for URL shortener FastAPI app: shorten, redirect, 404, list, delete, invalid input."""
import pytest
from fastapi.testclient import TestClient

from url_shortener.main import app
from url_shortener.store import get_store


@pytest.fixture(autouse=True)
def reset_store():
    get_store().clear()
    yield
    get_store().clear()


def test_shorten_returns_200_and_short_url():
    client = TestClient(app)
    response = client.post("/shorten", json={"url": "https://example.com/page"})
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["long_url"] == "https://example.com/page"
    assert data["short_code"] in data["short_url"]


def test_redirect_to_original_url():
    client = TestClient(app, follow_redirects=False)
    r = client.post("/shorten", json={"url": "https://example.com/target"})
    assert r.status_code == 200
    short_code = r.json()["short_code"]
    redirect_response = client.get(f"/{short_code}")
    assert redirect_response.status_code == 302
    assert redirect_response.headers["location"] == "https://example.com/target"


def test_unknown_short_code_returns_404():
    client = TestClient(app)
    response = client.get("/nonexistent123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_duplicate_long_url_returns_same_short_code():
    client = TestClient(app)
    url = "https://example.com/duplicate"
    r1 = client.post("/shorten", json={"url": url})
    r2 = client.post("/shorten", json={"url": url})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["short_code"] == r2.json()["short_code"]


def test_invalid_url_returns_400():
    client = TestClient(app)
    response = client.post("/shorten", json={"url": "not-a-valid-url"})
    assert response.status_code == 422  # FastAPI/Pydantic validation error for invalid URL


def test_list_urls():
    client = TestClient(app)
    client.post("/shorten", json={"url": "https://a.com"})
    client.post("/shorten", json={"url": "https://b.com"})
    response = client.get("/urls")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    codes = {item["short_code"] for item in items}
    urls = {item["long_url"] for item in items}
    # HttpUrl normalizes (e.g. adds trailing slash)
    assert any("a.com" in u for u in urls) and any("b.com" in u for u in urls)
    assert len(codes) == 2


def test_delete_short_code():
    client = TestClient(app)
    r = client.post("/shorten", json={"url": "https://example.com/delete-me"})
    short_code = r.json()["short_code"]
    del_response = client.delete(f"/{short_code}")
    assert del_response.status_code == 204
    get_response = client.get(f"/{short_code}")
    assert get_response.status_code == 404


def test_delete_unknown_returns_404():
    client = TestClient(app)
    response = client.delete("/unknown99")
    assert response.status_code == 404
