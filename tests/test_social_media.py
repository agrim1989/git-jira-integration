"""Tests for KAN-78 social media API: profiles, posts, feed, likes, comments, delete auth."""
import pytest
from fastapi.testclient import TestClient

from social_media.main import app
from social_media.store import get_store


@pytest.fixture(autouse=True)
def reset_store():
    store = get_store()
    store._users.clear()
    store._posts.clear()
    store._post_order.clear()
    store._likes.clear()
    store._comments.clear()
    store._comment_objs.clear()
    yield
    store._users.clear()
    store._posts.clear()
    store._post_order.clear()
    store._likes.clear()
    store._comments.clear()
    store._comment_objs.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_a(client):
    r = client.post("/users/register", json={"display_name": "User A", "bio": "Bio A"})
    assert r.status_code == 200
    return r.json()["user_id"]


@pytest.fixture
def user_b(client):
    r = client.post("/users/register", json={"display_name": "User B"})
    assert r.status_code == 200
    return r.json()["user_id"]


def test_register_user(client):
    r = client.post("/users/register", json={"display_name": "Alice", "bio": "Hello"})
    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data
    assert data["display_name"] == "Alice"
    assert data["bio"] == "Hello"


def test_get_profile(client, user_a):
    r = client.get("/users/me", headers={"X-User-Id": user_a})
    assert r.status_code == 200
    assert r.json()["user_id"] == user_a
    assert r.json()["display_name"] == "User A"


def test_get_user_public(client, user_a):
    r = client.get(f"/users/{user_a}", headers={"X-User-Id": user_a})
    assert r.status_code == 200
    assert r.json()["user_id"] == user_a


def test_create_post(client, user_a):
    r = client.post(
        "/posts",
        json={"text": "My first post"},
        headers={"X-User-Id": user_a},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "My first post"
    assert data["author_id"] == user_a
    assert data["like_count"] == 0
    assert data["comment_count"] == 0


def test_list_feed(client, user_a, user_b):
    client.post("/posts", json={"text": "Post 1"}, headers={"X-User-Id": user_a})
    client.post("/posts", json={"text": "Post 2"}, headers={"X-User-Id": user_b})
    r = client.get("/posts", headers={"X-User-Id": user_a})
    assert r.status_code == 200
    feed = r.json()
    assert len(feed) == 2
    assert feed[0]["text"] == "Post 2"
    assert feed[1]["text"] == "Post 1"


def test_get_single_post(client, user_a):
    cr = client.post("/posts", json={"text": "Single"}, headers={"X-User-Id": user_a})
    post_id = cr.json()["post_id"]
    r = client.get(f"/posts/{post_id}", headers={"X-User-Id": user_a})
    assert r.status_code == 200
    assert r.json()["text"] == "Single"
    assert r.json()["post_id"] == post_id


def test_like_unlike(client, user_a, user_b):
    cr = client.post("/posts", json={"text": "Like me"}, headers={"X-User-Id": user_a})
    post_id = cr.json()["post_id"]
    client.post(f"/posts/{post_id}/like", headers={"X-User-Id": user_b})
    r = client.get(f"/posts/{post_id}", headers={"X-User-Id": user_a})
    assert r.json()["like_count"] == 1
    client.delete(f"/posts/{post_id}/like", headers={"X-User-Id": user_b})
    r = client.get(f"/posts/{post_id}", headers={"X-User-Id": user_a})
    assert r.json()["like_count"] == 0


def test_add_and_list_comments(client, user_a, user_b):
    cr = client.post("/posts", json={"text": "Post"}, headers={"X-User-Id": user_a})
    post_id = cr.json()["post_id"]
    client.post(f"/posts/{post_id}/comments", json={"text": "Nice!"}, headers={"X-User-Id": user_b})
    r = client.get(f"/posts/{post_id}/comments", headers={"X-User-Id": user_a})
    assert r.status_code == 200
    comments = r.json()
    assert len(comments) == 1
    assert comments[0]["text"] == "Nice!"
    assert comments[0]["author_id"] == user_b


def test_delete_own_post(client, user_a):
    cr = client.post("/posts", json={"text": "Delete me"}, headers={"X-User-Id": user_a})
    post_id = cr.json()["post_id"]
    r = client.delete(f"/posts/{post_id}", headers={"X-User-Id": user_a})
    assert r.status_code == 204
    r = client.get(f"/posts/{post_id}", headers={"X-User-Id": user_a})
    assert r.status_code == 404


def test_cannot_delete_another_users_post(client, user_a, user_b):
    cr = client.post("/posts", json={"text": "User A post"}, headers={"X-User-Id": user_a})
    post_id = cr.json()["post_id"]
    r = client.delete(f"/posts/{post_id}", headers={"X-User-Id": user_b})
    assert r.status_code == 403
    r = client.get(f"/posts/{post_id}", headers={"X-User-Id": user_a})
    assert r.status_code == 200
