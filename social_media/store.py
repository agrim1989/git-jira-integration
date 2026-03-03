"""In-memory store for users, posts, likes, and comments."""
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class User:
    user_id: str
    display_name: str
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Post:
    post_id: str
    author_id: str
    text: str
    media_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Comment:
    comment_id: str
    post_id: str
    author_id: str
    text: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SocialStore:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._posts: dict[str, Post] = {}
        self._post_order: list[str] = []  # newest last, for feed
        self._likes: dict[str, set[str]] = {}  # post_id -> set of user_id
        self._comments: dict[str, list[str]] = {}  # post_id -> [comment_id, ...]
        self._comment_objs: dict[str, Comment] = {}

    def create_user(self, display_name: str, bio: str | None = None, avatar_url: str | None = None) -> User:
        user_id = str(uuid.uuid4())
        user = User(user_id=user_id, display_name=display_name, bio=bio, avatar_url=avatar_url)
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def create_post(self, author_id: str, text: str, media_url: str | None = None) -> Post:
        post_id = str(uuid.uuid4())
        post = Post(post_id=post_id, author_id=author_id, text=text, media_url=media_url)
        self._posts[post_id] = post
        self._post_order.append(post_id)
        self._likes[post_id] = set()
        self._comments[post_id] = []
        return post

    def get_post(self, post_id: str) -> Post | None:
        return self._posts.get(post_id)

    def delete_post(self, post_id: str, user_id: str) -> bool:
        post = self._posts.get(post_id)
        if not post or post.author_id != user_id:
            return False
        del self._posts[post_id]
        self._post_order = [p for p in self._post_order if p != post_id]
        self._likes.pop(post_id, None)
        for cid in self._comments.pop(post_id, []):
            self._comment_objs.pop(cid, None)
        return True

    def get_feed(self, limit: int = 20, offset: int = 0) -> list[Post]:
        ordered = list(reversed(self._post_order))
        slice_ids = ordered[offset : offset + limit]
        return [self._posts[pid] for pid in slice_ids if pid in self._posts]

    def like_post(self, post_id: str, user_id: str) -> bool:
        if post_id not in self._posts or user_id not in self._users:
            return False
        self._likes.setdefault(post_id, set()).add(user_id)
        return True

    def unlike_post(self, post_id: str, user_id: str) -> bool:
        if post_id not in self._likes:
            return False
        self._likes[post_id].discard(user_id)
        return True

    def get_like_count(self, post_id: str) -> int:
        return len(self._likes.get(post_id, set()))

    def add_comment(self, post_id: str, author_id: str, text: str) -> Comment | None:
        if post_id not in self._posts or author_id not in self._users:
            return None
        comment_id = str(uuid.uuid4())
        comment = Comment(comment_id=comment_id, post_id=post_id, author_id=author_id, text=text)
        self._comment_objs[comment_id] = comment
        self._comments.setdefault(post_id, []).append(comment_id)
        return comment

    def get_comment_count(self, post_id: str) -> int:
        return len(self._comments.get(post_id, []))

    def get_comments(self, post_id: str) -> list[Comment]:
        cids = self._comments.get(post_id, [])
        return [self._comment_objs[cid] for cid in cids if cid in self._comment_objs]


_store: SocialStore | None = None


def get_store() -> SocialStore:
    global _store
    if _store is None:
        _store = SocialStore()
    return _store
