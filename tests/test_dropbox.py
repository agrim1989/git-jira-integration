"""Tests for Dropbox-like API (KAN-80): auth, upload, download, list, folder, share."""
import io
import pytest
from fastapi.testclient import TestClient

from dropbox.main import app
from dropbox.store import get_store, reset_store_for_testing


@pytest.fixture(autouse=True)
def reset_store():
    reset_store_for_testing()
    yield
    reset_store_for_testing()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_headers():
    return {"X-User-Id": "user-1"}


def test_requires_auth(client):
    """Missing X-User-Id returns 401 or 422 (validation)."""
    r = client.get("/files/list")
    assert r.status_code in (401, 422)


def test_upload_and_download(client, user_headers):
    """Upload file then download returns same content."""
    r = client.post(
        "/files/upload",
        params={"path": "readme.txt"},
        files={"file": ("readme.txt", io.BytesIO(b"hello world"), "text/plain")},
        headers=user_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["path"] == "/readme.txt"
    assert data["size"] == 11
    r2 = client.get("/files/download/readme.txt", headers=user_headers)
    assert r2.status_code == 200
    assert r2.content == b"hello world"


def test_list_directory(client, user_headers):
    """Create folder and file; list shows them."""
    client.post("/files/folder", params={"path": "docs"}, headers=user_headers)
    client.post(
        "/files/upload",
        params={"path": "docs/a.txt"},
        files={"file": ("a.txt", io.BytesIO(b"a"), "text/plain")},
        headers=user_headers,
    )
    r = client.get("/files/list", params={"path": "/"}, headers=user_headers)
    assert r.status_code == 200
    entries = r.json()
    assert len(entries) >= 1
    names = [e["name"] for e in entries]
    assert "docs" in names


def test_create_folder(client, user_headers):
    """Create folder returns success."""
    r = client.post("/files/folder", params={"path": "photos"}, headers=user_headers)
    assert r.status_code == 200
    assert r.json()["created"] is True


def test_delete_file(client, user_headers):
    """Upload then delete file."""
    client.post(
        "/files/upload",
        params={"path": "todel.txt"},
        files={"file": ("todel.txt", io.BytesIO(b"x"), "text/plain")},
        headers=user_headers,
    )
    r = client.delete("/files/todel.txt", headers=user_headers)
    assert r.status_code == 200
    r2 = client.get("/files/download/todel.txt", headers=user_headers)
    assert r2.status_code == 404


def test_share_create_and_access(client, user_headers):
    """Create share link and download via token."""
    client.post(
        "/files/upload",
        params={"path": "shared.txt"},
        files={"file": ("shared.txt", io.BytesIO(b"secret"), "text/plain")},
        headers=user_headers,
    )
    r = client.post("/share", json={"path": "/shared.txt"}, headers=user_headers)
    assert r.status_code == 200
    token = r.json()["token"]
    r2 = client.get(f"/share/{token}")
    assert r2.status_code == 200
    assert r2.content == b"secret"


def test_download_nonexistent_returns_404(client, user_headers):
    r = client.get("/files/download/nonexistent.txt", headers=user_headers)
    assert r.status_code == 404


def test_share_nonexistent_returns_404(client, user_headers):
    r = client.post("/share", json={"path": "/nonexistent.txt"}, headers=user_headers)
    assert r.status_code == 404
