"""Social media API: profiles, posts, feed, likes, comments. KAN-78."""
from fastapi import FastAPI, Header, HTTPException

from social_media.models import (
    CommentCreate,
    CommentResponse,
    PostCreate,
    PostResponse,
    UserCreate,
    UserResponse,
)
from social_media.store import get_store

USER_HEADER = "x-user-id"


def get_user_id(x_user_id: str | None = Header(default=None, alias=USER_HEADER)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    store = get_store()
    if not store.get_user(x_user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return x_user_id


app = FastAPI(
    title="Social Media API (KAN-78)",
    description="Profiles, posts, feed, likes, comments.",
)


# ----- Users -----
@app.post("/users/register", response_model=UserResponse)
def register(body: UserCreate):
    store = get_store()
    user = store.create_user(body.display_name, body.bio, body.avatar_url)
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
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
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    store = get_store()
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        bio=user.bio,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


# ----- Posts -----
@app.post("/posts", response_model=PostResponse)
def create_post(body: PostCreate, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    post = store.create_post(user_id, body.text, body.media_url)
    return PostResponse(
        post_id=post.post_id,
        author_id=post.author_id,
        text=post.text,
        media_url=post.media_url,
        created_at=post.created_at,
        like_count=0,
        comment_count=0,
    )


@app.get("/posts", response_model=list[PostResponse])
def list_feed(limit: int = 20, offset: int = 0, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    posts = store.get_feed(limit=limit, offset=offset)
    return [
        PostResponse(
            post_id=p.post_id,
            author_id=p.author_id,
            text=p.text,
            media_url=p.media_url,
            created_at=p.created_at,
            like_count=store.get_like_count(p.post_id),
            comment_count=store.get_comment_count(p.post_id),
        )
        for p in posts
    ]


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    post = store.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse(
        post_id=post.post_id,
        author_id=post.author_id,
        text=post.text,
        media_url=post.media_url,
        created_at=post.created_at,
        like_count=store.get_like_count(post_id),
        comment_count=store.get_comment_count(post_id),
    )


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: str, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    if not store.delete_post(post_id, user_id):
        raise HTTPException(status_code=403, detail="Not your post or post not found")
    return None


# ----- Likes -----
@app.post("/posts/{post_id}/like", status_code=204)
def like_post(post_id: str, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    if not store.like_post(post_id, user_id):
        raise HTTPException(status_code=404, detail="Post or user not found")
    return None


@app.delete("/posts/{post_id}/like", status_code=204)
def unlike_post(post_id: str, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    store.unlike_post(post_id, user_id)
    return None


# ----- Comments -----
@app.post("/posts/{post_id}/comments", response_model=CommentResponse)
def add_comment(post_id: str, body: CommentCreate, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    comment = store.add_comment(post_id, user_id, body.text)
    if not comment:
        raise HTTPException(status_code=404, detail="Post or user not found")
    return CommentResponse(
        comment_id=comment.comment_id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        text=comment.text,
        created_at=comment.created_at,
    )


@app.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def list_comments(post_id: str, user_id: str = Header(..., alias=USER_HEADER)):
    store = get_store()
    if not store.get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    comments = store.get_comments(post_id)
    return [
        CommentResponse(
            comment_id=c.comment_id,
            post_id=c.post_id,
            author_id=c.author_id,
            text=c.text,
            created_at=c.created_at,
        )
        for c in comments
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
