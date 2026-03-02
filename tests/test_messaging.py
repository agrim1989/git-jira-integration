"""Tests for KAN-71 messaging API: users, conversations, messages, WebSocket."""
import json

import pytest
from fastapi.testclient import TestClient

from messaging.main import app
from messaging.store import get_store


@pytest.fixture(autouse=True)
def reset_store():
    store = get_store()
    store._users.clear()
    store._conversations.clear()
    store._messages.clear()
    store._conv_messages.clear()
    store._user_conversations.clear()
    # Re-seed System user so /users/me can be used
    store.create_user("System")
    yield
    store._users.clear()
    store._conversations.clear()
    store._messages.clear()
    store._conv_messages.clear()
    store._user_conversations.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_a(client):
    r = client.post("/users/register", json={"display_name": "User A"})
    assert r.status_code == 200
    return r.json()["user_id"]


@pytest.fixture
def user_b(client):
    r = client.post("/users/register", json={"display_name": "User B"})
    assert r.status_code == 200
    return r.json()["user_id"]


def test_register_user(client):
    r = client.post("/users/register", json={"display_name": "Alice"})
    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data
    assert data["display_name"] == "Alice"


def test_get_me(client, user_a):
    r = client.get("/users/me", headers={"X-User-Id": user_a})
    assert r.status_code == 200
    assert r.json()["user_id"] == user_a
    assert r.json()["display_name"] == "User A"


def test_get_me_unauthorized(client):
    r = client.get("/users/me")
    assert r.status_code == 422  # missing header


def test_create_conversation_1_to_1(client, user_a, user_b):
    r = client.post(
        "/conversations",
        json={"participant_ids": [user_b], "name": None},
        headers={"X-User-Id": user_a},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["participant_ids"] == [user_a, user_b] or user_b in data["participant_ids"]
    conv_id = data["conversation_id"]
    assert len(conv_id) > 0


def test_send_and_list_messages(client, user_a, user_b):
    cr = client.post(
        "/conversations",
        json={"participant_ids": [user_b], "name": None},
        headers={"X-User-Id": user_a},
    )
    conv_id = cr.json()["conversation_id"]
    sr = client.post(
        f"/conversations/{conv_id}/messages",
        json={"text": "Hello"},
        headers={"X-User-Id": user_a},
    )
    assert sr.status_code == 200
    assert sr.json()["text"] == "Hello"
    lr = client.get(f"/conversations/{conv_id}/messages", headers={"X-User-Id": user_a})
    assert lr.status_code == 200
    msgs = lr.json()
    assert len(msgs) == 1
    assert msgs[0]["text"] == "Hello"
    assert msgs[0]["sender_id"] == user_a


def test_list_conversations(client, user_a, user_b):
    client.post(
        "/conversations",
        json={"participant_ids": [user_b], "name": None},
        headers={"X-User-Id": user_a},
    )
    r = client.get("/conversations", headers={"X-User-Id": user_a})
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_mark_message_read(client, user_a, user_b):
    cr = client.post(
        "/conversations",
        json={"participant_ids": [user_b], "name": None},
        headers={"X-User-Id": user_a},
    )
    conv_id = cr.json()["conversation_id"]
    sr = client.post(
        f"/conversations/{conv_id}/messages",
        json={"text": "Hi"},
        headers={"X-User-Id": user_a},
    )
    msg_id = sr.json()["message_id"]
    r = client.patch(
        f"/conversations/{conv_id}/messages/{msg_id}/read",
        json={"read": True},
        headers={"X-User-Id": user_b},
    )
    assert r.status_code == 204


def test_websocket_send_message(client, user_a, user_b):
    # Create conversation via REST
    cr = client.post(
        "/conversations",
        json={"participant_ids": [user_b], "name": None},
        headers={"X-User-Id": user_a},
    )
    conv_id = cr.json()["conversation_id"]
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"user_id": user_a}))
        data = json.loads(ws.receive_text())
        assert data.get("status") == "connected"
        ws.send_text(json.dumps({"conversation_id": conv_id, "text": "WS hello"}))
        out = json.loads(ws.receive_text())
        assert "message_id" in out
        assert out["text"] == "WS hello"
        assert out["sender_id"] == user_a
