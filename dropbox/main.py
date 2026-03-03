"""Dropbox-like file storage API. KAN-80."""
import logging
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse, Response

from dropbox.models import FileMetadataResponse, ListEntry, ShareCreate, ShareResponse
from dropbox.store import get_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_HEADER = "x-user-id"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def get_user_id(x_user_id: str | None = Header(default=None, alias=USER_HEADER)) -> str:
    """Require X-User-Id header for auth."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return x_user_id


app = FastAPI(
    title="Dropbox-like API (KAN-80)",
    description="File upload, download, list, folders, sharing.",
)


@app.post("/files/upload", response_model=FileMetadataResponse)
def upload_file(
    path: str,
    user_id: str = Header(..., alias=USER_HEADER),
    file: UploadFile = File(...),
):
    """Upload a file to the given path (e.g. /docs/readme.txt)."""
    if not path or not path.strip("/"):
        raise HTTPException(status_code=400, detail="path required")
    if ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_SIZE} bytes)")
    store = get_store()
    store.ensure_folder(user_id, str(__import__("pathlib").Path(path).parent))
    meta = store.put_file(user_id, path.strip("/"), content, file.content_type or "application/octet-stream")
    return FileMetadataResponse(
        path=meta.path,
        owner_id=meta.owner_id,
        size=meta.size,
        content_type=meta.content_type,
        created_at=meta.created_at,
        updated_at=meta.updated_at,
        is_folder=meta.is_folder,
    )


@app.get("/files/download/{path:path}")
def download_file(path: str, user_id: str = Header(..., alias=USER_HEADER)):
    """Download file at path. Returns 404 if not found."""
    store = get_store()
    content = store.get_file(user_id, path)
    if content is None:
        raise HTTPException(status_code=404, detail="Not found")
    meta = store.get_metadata(user_id, path)
    if not meta:
        raise HTTPException(status_code=404, detail="Not found")
    return Response(content=content, media_type=meta.content_type)


def _norm_path(path: str) -> str:
    p = path.strip().strip("/") or ""
    return "/" + p if p else "/"


@app.get("/files/list", response_model=list[ListEntry])
def list_files(path: str = "/", user_id: str = Header(..., alias=USER_HEADER)):
    """List directory contents at path."""
    store = get_store()
    norm = _norm_path(path)
    entries = store.list_dir(user_id, norm)
    return [
        ListEntry(
            path=e.path,
            name=e.path.rstrip("/").split("/")[-1] or "/",
            is_folder=e.is_folder,
            size=e.size if not e.is_folder else None,
            updated_at=e.updated_at,
        )
        for e in entries
    ]


@app.post("/files/folder")
def create_folder(path: str, user_id: str = Header(..., alias=USER_HEADER)):
    """Create a folder at path."""
    if not path or ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path")
    store = get_store()
    store.ensure_folder(user_id, path.strip("/"))
    return {"path": _norm_path(path), "created": True}


@app.delete("/files/{path:path}")
def delete_path(path: str, user_id: str = Header(..., alias=USER_HEADER)):
    """Delete file or empty folder."""
    store = get_store()
    ok = store.delete(user_id, path)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found or not empty")
    return {"deleted": True}


@app.post("/share", response_model=ShareResponse)
def create_share(body: ShareCreate, user_id: str = Header(..., alias=USER_HEADER)):
    """Create a share link for path."""
    store = get_store()
    try:
        share = store.create_share(user_id, body.path, body.expires_in_hours)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    base = "http://localhost:8000"  # config in real app
    return ShareResponse(
        path=share.path,
        token=share.token,
        share_url=f"{base}/share/{share.token}",
        expires_at=share.expires_at,
    )


@app.get("/share/{token}")
def access_share(token: str):
    """Download file via share token."""
    store = get_store()
    result = store.get_file_via_share(token)
    if result is None:
        raise HTTPException(status_code=404, detail="Not found or expired")
    content, content_type = result
    return Response(content=content, media_type=content_type)
