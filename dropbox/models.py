"""Pydantic models for Dropbox-like API. KAN-80."""
from datetime import datetime
from pydantic import BaseModel, Field


class FileMetadataResponse(BaseModel):
    """Metadata for a stored file."""

    path: str
    owner_id: str
    size: int
    content_type: str
    created_at: datetime
    updated_at: datetime
    is_folder: bool = False


class ListEntry(BaseModel):
    """Single entry in directory listing."""

    path: str
    name: str
    is_folder: bool
    size: int | None = None
    updated_at: datetime | None = None


class ShareCreate(BaseModel):
    """Request to create a share link."""

    path: str
    expires_in_hours: int | None = Field(default=None, description="None = no expiry")


class ShareResponse(BaseModel):
    """Response with share URL/token."""

    path: str
    token: str
    share_url: str
    expires_at: datetime | None = None
