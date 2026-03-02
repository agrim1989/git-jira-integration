"""In-memory store for users, conversations, messages, and delivery/read state."""
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class User:
    user_id: str
    display_name: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Conversation:
    conversation_id: str
    participant_ids: list[str]
    name: str | None  # None = 1:1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Message:
    message_id: str
    conversation_id: str
    sender_id: str
    text: str
    sent_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class MessagingStore:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._conversations: dict[str, Conversation] = {}
        self._messages: dict[str, Message] = {}
        self._conv_messages: dict[str, list[str]] = {}  # conv_id -> [msg_id, ...]
        self._user_conversations: dict[str, list[str]] = {}  # user_id -> [conv_id, ...]

    def create_user(self, display_name: str) -> User:
        user_id = str(uuid.uuid4())
        user = User(user_id=user_id, display_name=display_name)
        self._users[user_id] = user
        self._user_conversations[user_id] = []
        return user

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def create_conversation(self, participant_ids: list[str], name: str | None = None) -> Conversation:
        conv_id = str(uuid.uuid4())
        conv = Conversation(conversation_id=conv_id, participant_ids=list(participant_ids), name=name)
        self._conversations[conv_id] = conv
        self._conv_messages[conv_id] = []
        for uid in participant_ids:
            self._user_conversations.setdefault(uid, []).append(conv_id)
        return conv

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)

    def get_user_conversations(self, user_id: str) -> list[Conversation]:
        conv_ids = self._user_conversations.get(user_id, [])
        return [self._conversations[cid] for cid in conv_ids if cid in self._conversations]

    def add_message(self, conversation_id: str, sender_id: str, text: str) -> Message:
        msg_id = str(uuid.uuid4())
        msg = Message(message_id=msg_id, conversation_id=conversation_id, sender_id=sender_id, text=text)
        self._messages[msg_id] = msg
        self._conv_messages.setdefault(conversation_id, []).append(msg_id)
        return msg

    def get_message(self, message_id: str) -> Message | None:
        return self._messages.get(message_id)

    def get_conversation_messages(
        self, conversation_id: str, limit: int = 50, before_msg_id: str | None = None
    ) -> list[Message]:
        msg_ids = self._conv_messages.get(conversation_id, [])
        if before_msg_id and before_msg_id in msg_ids:
            idx = msg_ids.index(before_msg_id)
            msg_ids = msg_ids[:idx]
        msg_ids = msg_ids[-limit:]
        return [self._messages[mid] for mid in reversed(msg_ids) if mid in self._messages]

    def mark_delivered(self, message_id: str) -> None:
        if msg := self._messages.get(message_id):
            if msg.delivered_at is None:
                msg.delivered_at = datetime.now(UTC)

    def mark_read(self, message_id: str) -> None:
        if msg := self._messages.get(message_id):
            if msg.read_at is None:
                msg.read_at = datetime.now(UTC)

    def user_in_conversation(self, user_id: str, conversation_id: str) -> bool:
        conv = self._conversations.get(conversation_id)
        return conv is not None and user_id in conv.participant_ids


_store: MessagingStore | None = None


def get_store() -> MessagingStore:
    global _store
    if _store is None:
        _store = MessagingStore()
    return _store
