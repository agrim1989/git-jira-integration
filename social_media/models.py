"""Pydantic models for social media API."""
from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)
    avatar_url: str | None = Field(default=None, max_length=2048)


class UserResponse(BaseModel):
    user_id: str
    display_name: str
    bio: str | None
    avatar_url: str | None
    created_at: datetime


class PostCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=64 * 1024)
    media_url: str | None = Field(default=None, max_length=2048)


class PostResponse(BaseModel):
    post_id: str
    author_id: str
    text: str
    media_url: str | None
    created_at: datetime
    like_count: int
    comment_count: int


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)


class CommentResponse(BaseModel):
    comment_id: str
    post_id: str
    author_id: str
    text: str
    created_at: datetime
