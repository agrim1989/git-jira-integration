"""Tests for marketplace API (KAN-81): auth, products, cart, checkout, orders."""
import pytest
from fastapi.testclient import TestClient

from marketplace.main import app
from marketplace.store import reset_store_for_testing


@pytest.fixture(autouse=True)
def reset_store():
    reset_store_for_testing()
    yield
    reset_store_for_testing()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user(client):
    r = client.post("/users/register", json={"email": "buyer@test.com", "name": "Buyer"})
    assert r.status_code == 200
    return r.json()["user_id"]


@pytest.fixture
def headers(user):
    return {"X-User-Id": user}


def test_auth_required(client):
    r = client.get("/cart")
    assert r.status_code in (401, 422)


def test_register_and_get_me(client, user, headers):
    r = client.get("/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "buyer@test.com"


def test_list_products(client):
    r = client.get("/products")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 3


def test_list_products_filter_by_category(client):
    r = client.get("/products", params={"category_id": "cat-1"})
    assert r.status_code == 200
    for p in r.json():
        assert p["category_id"] == "cat-1"


def test_get_product(client):
    r = client.get("/products/p1")
    assert r.status_code == 200
    assert r.json()["title"] == "Widget A"


def test_add_to_cart(client, headers):
    r = client.post("/cart", json={"product_id": "p1", "quantity": 2}, headers=headers)
    assert r.status_code == 200
    r2 = client.get("/cart", headers=headers)
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["product_id"] == "p1"
    assert items[0]["quantity"] == 2


def test_cart_update_and_remove(client, headers):
    client.post("/cart", json={"product_id": "p1", "quantity": 1}, headers=headers)
    r = client.patch("/cart/p1", params={"quantity": 3}, headers=headers)
    assert r.status_code == 200
    r2 = client.get("/cart", headers=headers)
    assert r2.json()[0]["quantity"] == 3
    client.delete("/cart/p1", headers=headers)
    r3 = client.get("/cart", headers=headers)
    assert r3.json() == []


def test_checkout_creates_order_and_clears_cart(client, headers):
    client.post("/cart", json={"product_id": "p1", "quantity": 1}, headers=headers)
    client.post("/cart", json={"product_id": "p2", "quantity": 1}, headers=headers)
    r = client.post("/orders", headers=headers)
    assert r.status_code == 200
    order = r.json()
    assert "order_id" in order
    assert order["total"] > 0
    assert len(order["items"]) == 2
    r2 = client.get("/cart", headers=headers)
    assert r2.json() == []
    r3 = client.get("/orders", headers=headers)
    assert len(r3.json()) == 1


def test_get_order(client, headers):
    client.post("/cart", json={"product_id": "p1", "quantity": 1}, headers=headers)
    r = client.post("/orders", headers=headers)
    order_id = r.json()["order_id"]
    r2 = client.get(f"/orders/{order_id}", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["order_id"] == order_id


def test_checkout_empty_cart_returns_400(client, headers):
    r = client.post("/orders", headers=headers)
    assert r.status_code == 400
