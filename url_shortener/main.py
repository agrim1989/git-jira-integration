"""FastAPI URL shortener: POST /shorten, GET /{short_code} redirect, GET /urls, DELETE /{short_code}."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

from url_shortener.store import get_store

app = FastAPI(title="URL Shortener", description="Shorten URLs and redirect by short code.")

MAX_URL_LEN = 2048


class ShortenRequest(BaseModel):
    url: HttpUrl = Field(..., description="Long URL to shorten")

    model_config = {"json_schema_extra": {"example": {"url": "https://example.com/page"}}}


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str


class UrlItem(BaseModel):
    short_code: str
    long_url: str


def _base_url_from_request(request) -> str:
    """Base URL for building short_url (e.g. http://localhost:8000)."""
    return str(request.base_url).rstrip("/")


@app.post("/shorten", response_model=ShortenResponse)
def shorten(body: ShortenRequest, req: Request):
    long_url = str(body.url)
    if len(long_url) > MAX_URL_LEN:
        raise HTTPException(status_code=400, detail="URL too long")
    store = get_store()
    short_code = store.add(long_url)
    base = _base_url_from_request(req)
    return ShortenResponse(
        short_code=short_code,
        short_url=f"{base}/{short_code}",
        long_url=long_url,
    )


@app.get("/urls", response_model=list[UrlItem])
def list_urls():
    store = get_store()
    return [UrlItem(short_code=c, long_url=u) for c, u in store.list_all()]


@app.get("/{short_code}", status_code=302)
def redirect(short_code: str):
    store = get_store()
    long_url = store.get(short_code)
    if long_url is None:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url=long_url, status_code=302)


@app.delete("/{short_code}", status_code=204)
def delete_url(short_code: str):
    store = get_store()
    if not store.delete(short_code):
        raise HTTPException(status_code=404, detail="Short code not found")
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
