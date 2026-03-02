"""In-memory store for short_code -> long_url mappings with base62 short codes."""
import random
import string

# base62 alphabet (0-9, a-z, A-Z)
BASE62 = string.digits + string.ascii_lowercase + string.ascii_uppercase
DEFAULT_CODE_LEN = 6
MAX_URL_LEN = 2048


def _random_code(length: int = DEFAULT_CODE_LEN) -> str:
    return "".join(random.choices(BASE62, k=length))


class UrlStore:
    def __init__(self, code_length: int = DEFAULT_CODE_LEN):
        self._code_to_url: dict[str, str] = {}
        self._url_to_code: dict[str, str] = {}
        self._code_length = code_length

    def add(self, long_url: str) -> str:
        long_url = long_url.strip()
        if long_url in self._url_to_code:
            return self._url_to_code[long_url]
        while True:
            code = _random_code(self._code_length)
            if code not in self._code_to_url:
                break
        self._code_to_url[code] = long_url
        self._url_to_code[long_url] = code
        return code

    def get(self, short_code: str) -> str | None:
        return self._code_to_url.get(short_code)

    def delete(self, short_code: str) -> bool:
        if short_code not in self._code_to_url:
            return False
        long_url = self._code_to_url.pop(short_code)
        self._url_to_code.pop(long_url, None)
        return True

    def list_all(self) -> list[tuple[str, str]]:
        return list(self._code_to_url.items())

    def clear(self) -> None:
        """Clear all mappings (for tests)."""
        self._code_to_url.clear()
        self._url_to_code.clear()


_store: UrlStore | None = None


def get_store() -> UrlStore:
    global _store
    if _store is None:
        _store = UrlStore()
    return _store
