"""Pydantic models for messaging API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)


class UserResponse(BaseModel):
    user_id: str
    display_name: str
    created_at: datetime


class ConversationCreate(BaseModel):
    participant_ids: list[str] = Field(..., min_length=1)
    name: str | None = None  # for group; None = 1:1


class ConversationResponse(BaseModel):
    conversation_id: str
    participant_ids: list[str]
    name: str | None
    created_at: datetime


class MessageSend(BaseModel):
    text: str = Field(..., min_length=1, max_length=64 * 1024)


class MessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    sender_id: str
    text: str
    sent_at: datetime
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class MessageReadUpdate(BaseModel):
    read: bool = True
