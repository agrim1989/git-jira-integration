"""WhatsApp-like messaging API: REST + WebSocket. Jira: KAN-71."""
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect

from messaging.models import (
    ConversationCreate,
    ConversationResponse,
    MessageReadUpdate,
    MessageResponse,
    MessageSend,
    UserCreate,
    UserResponse,
)
from messaging.store import get_store

# Simple auth for POC: X-User-Id header
USER_HEADER = "x-user-id"


def get_current_user_id(x_user_id: str | None = Header(default=None, alias=USER_HEADER)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    store = get_store()
    if not store.get_user(x_user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return x_user_id


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Optional: seed a default user for testing
    store = get_store()
    if not store._users:
        store.create_user("System")
    yield


app = FastAPI(
    title="Messaging API (KAN-71)",
    description="WhatsApp-like messaging: 1:1 and group chats, real-time WebSocket, delivery/read state.",
    lifespan=lifespan,
)


# ----- Users -----
@app.post("/users/register", response_model=UserResponse)
def register_user(body: UserCreate):
    store = get_store()
    user = store.create_user(body.display_name)
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        created_at=user.created_at,
    )


@app.get("/users/me", response_model=UserResponse)
def get_me(user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        created_at=user.created_at,
    )


# ----- Conversations -----
@app.post("/conversations", response_model=ConversationResponse)
def create_conversation(body: ConversationCreate, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    if user_id not in body.participant_ids:
        body.participant_ids = [user_id] + [p for p in body.participant_ids if p != user_id]
    for pid in body.participant_ids:
        if not store.get_user(pid):
            raise HTTPException(status_code=400, detail=f"Unknown participant: {pid}")
    conv = store.create_conversation(body.participant_ids, body.name)
    return ConversationResponse(
        conversation_id=conv.conversation_id,
        participant_ids=conv.participant_ids,
        name=conv.name,
        created_at=conv.created_at,
    )


@app.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    convs = store.get_user_conversations(user_id)
    return [
        ConversationResponse(
            conversation_id=c.conversation_id,
            participant_ids=c.participant_ids,
            name=c.name,
            created_at=c.created_at,
        )
        for c in convs
    ]


# ----- Messages -----
@app.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: str,
    limit: int = 50,
    before: str | None = None,
    user_id: str = Header(..., alias=USER_HEADER),
):
    store = get_store()
    if not store.user_in_conversation(user_id, conversation_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    msgs = store.get_conversation_messages(conversation_id, limit=limit, before_msg_id=before)
    return [
        MessageResponse(
            message_id=m.message_id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            text=m.text,
            sent_at=m.sent_at,
            delivered_at=m.delivered_at,
            read_at=m.read_at,
        )
        for m in msgs
    ]


@app.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: str,
    body: MessageSend,
    user_id: str = Header(..., alias=USER_HEADER),
):
    store = get_store()
    if not store.user_in_conversation(user_id, conversation_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    msg = store.add_message(conversation_id, user_id, body.text)
    return MessageResponse(
        message_id=msg.message_id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        text=msg.text,
        sent_at=msg.sent_at,
        delivered_at=msg.delivered_at,
        read_at=msg.read_at,
    )


@app.patch("/conversations/{conversation_id}/messages/{message_id}/read", status_code=204)
def mark_message_read(
    conversation_id: str,
    message_id: str,
    body: MessageReadUpdate,
    user_id: str = Header(..., alias=USER_HEADER),
):
    store = get_store()
    if not store.user_in_conversation(user_id, conversation_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    msg = store.get_message(message_id)
    if not msg or msg.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Message not found")
    if body.read:
        store.mark_read(message_id)
    return None


# ----- WebSocket -----
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id: str | None = None
    store = get_store()
    try:
        # First message must be {"user_id": "..."} to authenticate
        data = await websocket.receive_text()
        payload = json.loads(data)
        user_id = payload.get("user_id")
        if not user_id or not store.get_user(user_id):
            await websocket.send_json({"error": "Invalid or missing user_id"})
            await websocket.close(code=4008)
            return
        await websocket.send_json({"status": "connected", "user_id": user_id})

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if "conversation_id" in msg and "text" in msg:
                if not store.user_in_conversation(user_id, msg["conversation_id"]):
                    await websocket.send_json({"error": "Not a participant"})
                    continue
                m = store.add_message(msg["conversation_id"], user_id, msg["text"])
                await websocket.send_json(
                    {
                        "message_id": m.message_id,
                        "conversation_id": m.conversation_id,
                        "sender_id": m.sender_id,
                        "text": m.text,
                        "sent_at": m.sent_at.isoformat(),
                    }
                )
            else:
                await websocket.send_json({"error": "Expected conversation_id and text"})
    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError:
        try:
            await websocket.send_json({"error": "Invalid JSON"})
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
