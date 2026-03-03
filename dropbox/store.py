"""Metadata store and file storage backend for Dropbox-like API. KAN-80."""
import logging
import os
import secrets
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FileMeta:
    """Internal file metadata."""

    path: str
    owner_id: str
    size: int
    content_type: str
    created_at: datetime
    updated_at: datetime
    is_folder: bool = False
    blob_path: str | None = None  # physical path or key


@dataclass
class ShareRecord:
    """Share link record."""

    path: str
    owner_id: str
    token: str
    expires_at: datetime | None
    created_at: datetime


def _norm_path(path: str) -> str:
    """Normalize path: leading slash, no trailing slash for files."""
    path = path.strip().strip("/") or ""
    return "/" + path if path else "/"


class Store:
    """In-memory metadata store and optional disk storage for files."""

    def __init__(self, storage_root: str | None = None):
        self._meta: dict[str, FileMeta] = {}  # path -> FileMeta
        self._shares: dict[str, ShareRecord] = {}  # token -> ShareRecord
        self._storage_root = storage_root or tempfile.mkdtemp(prefix="dropbox_")
        Path(self._storage_root).mkdir(parents=True, exist_ok=True)
        logger.info("Store initialized with storage_root=%s", self._storage_root)

    def _blob_path(self, owner_id: str, path: str) -> Path:
        """Physical path for a file (owner_id + path)."""
        safe = path.strip("/").replace("..", "").replace("/", os.sep) or "root"
        return Path(self._storage_root) / owner_id / safe

    def ensure_folder(self, owner_id: str, path: str) -> None:
        """Ensure folder exists in metadata and on disk."""
        norm = _norm_path(path)
        if norm in self._meta:
            return
        self._meta[norm] = FileMeta(
            path=norm,
            owner_id=owner_id,
            size=0,
            content_type="application/x-directory",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_folder=True,
        )
        self._blob_path(owner_id, norm).mkdir(parents=True, exist_ok=True)

    def put_file(
        self,
        owner_id: str,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> FileMeta:
        """Store file; create parent folders if needed."""
        norm = _norm_path(path)
        parent = str(Path(norm).parent).replace("\\", "/") or "/"
        if parent != "/":
            self.ensure_folder(owner_id, parent)
        blob = self._blob_path(owner_id, norm)
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(content)
        now = datetime.utcnow()
        meta = FileMeta(
            path=norm,
            owner_id=owner_id,
            size=len(content),
            content_type=content_type,
            created_at=now,
            updated_at=now,
            is_folder=False,
            blob_path=str(blob),
        )
        self._meta[norm] = meta
        return meta

    def get_metadata(self, owner_id: str, path: str) -> FileMeta | None:
        """Get file metadata if exists and owned by user."""
        norm = _norm_path(path)
        meta = self._meta.get(norm)
        if not meta or meta.owner_id != owner_id:
            return None
        return meta

    def get_file(self, owner_id: str, path: str) -> bytes | None:
        """Return file content or None."""
        norm = _norm_path(path)
        meta = self._meta.get(norm)
        if not meta or meta.is_folder:
            return None
        if meta.owner_id != owner_id:
            return None
        blob = Path(meta.blob_path or self._blob_path(owner_id, norm))
        if not blob.exists():
            return None
        return blob.read_bytes()

    def get_file_via_share(self, token: str) -> tuple[bytes, str] | None:
        """Return (content, content_type) for share token or None."""
        share = self._shares.get(token)
        if not share:
            return None
        if share.expires_at and datetime.utcnow() > share.expires_at:
            return None
        meta = self._meta.get(share.path)
        if not meta or meta.is_folder:
            return None
        blob = Path(meta.blob_path or self._blob_path(meta.owner_id, meta.path))
        if not blob.exists():
            return None
        return blob.read_bytes(), meta.content_type

    def list_dir(self, owner_id: str, path: str) -> list[FileMeta]:
        """List direct children of path."""
        norm = _norm_path(path)
        prefix = norm.rstrip("/") + "/" if norm != "/" else "/"
        out: list[FileMeta] = []
        seen: set[str] = set()
        for p, m in self._meta.items():
            if m.owner_id != owner_id:
                continue
            if not p.startswith(prefix):
                continue
            rest = p[len(prefix) :].strip("/").split("/")[0]
            if not rest:
                continue
            child_path = prefix + rest
            if child_path in seen:
                continue
            seen.add(child_path)
            if child_path in self._meta:
                out.append(self._meta[child_path])
        return sorted(out, key=lambda x: (x.is_folder, x.path))

    def delete(self, owner_id: str, path: str) -> bool:
        """Remove file or empty folder. Returns True if removed."""
        norm = _norm_path(path)
        meta = self._meta.get(norm)
        if not meta or meta.owner_id != owner_id:
            return False
        if meta.is_folder:
            children = self.list_dir(owner_id, norm)
            if children:
                return False
        elif meta.blob_path:
            Path(meta.blob_path).unlink(missing_ok=True)
        del self._meta[norm]
        return True

    def create_share(self, owner_id: str, path: str, expires_in_hours: int | None) -> ShareRecord:
        """Create share link for path."""
        norm = _norm_path(path)
        if norm not in self._meta or self._meta[norm].owner_id != owner_id:
            raise ValueError("Path not found or not owned by user")
        expires = (datetime.utcnow() + timedelta(hours=expires_in_hours)) if expires_in_hours else None
        token = secrets.token_urlsafe(16)
        share = ShareRecord(path=norm, owner_id=owner_id, token=token, expires_at=expires, created_at=datetime.utcnow())
        self._shares[token] = share
        return share

    def get_share(self, token: str) -> ShareRecord | None:
        """Get share record by token."""
        s = self._shares.get(token)
        if not s or (s.expires_at and datetime.utcnow() > s.expires_at):
            return None
        return s


_store: Store | None = None


def get_store(storage_root: str | None = None) -> Store:
    """Singleton store instance."""
    global _store
    if _store is None:
        _store = Store(storage_root=storage_root)
    return _store


def reset_store_for_testing() -> None:
    """Clear singleton and in-memory state for tests."""
    global _store
    if _store is not None:
        _store._meta.clear()
        _store._shares.clear()
