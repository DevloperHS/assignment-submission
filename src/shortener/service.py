"""Core business logic for shortening and resolving URLs."""
from __future__ import annotations

import re
import secrets
import string
from typing import Callable, Optional
from urllib.parse import urlparse

from .storage import ShortUrl, UrlRepository

ALPHABET = string.ascii_letters + string.digits
ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
MAX_URL_LENGTH = 2048


class ShortenerError(Exception):
    """Base class for domain errors."""


class InvalidUrlError(ShortenerError):
    pass


class InvalidAliasError(ShortenerError):
    pass


class AliasTakenError(ShortenerError):
    pass


class CodeNotFoundError(ShortenerError):
    pass


class CodeGenerationError(ShortenerError):
    pass


def validate_url(url: str) -> str:
    url = url.strip()
    if not url or len(url) > MAX_URL_LENGTH:
        raise InvalidUrlError("URL must be 1-2048 characters")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidUrlError("URL must be an absolute http(s) URL")
    return url


def random_code(length: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


class ShortenerService:
    def __init__(
        self,
        repo: UrlRepository,
        code_length: int = 7,
        max_retries: int = 5,
        code_factory: Callable[[int], str] = random_code,
    ) -> None:
        self._repo = repo
        self._code_length = code_length
        self._max_retries = max_retries
        self._code_factory = code_factory

    def shorten(self, url: str, alias: Optional[str] = None) -> ShortUrl:
        url = validate_url(url)

        if alias is not None:
            if not ALIAS_PATTERN.match(alias):
                raise InvalidAliasError("Alias must be 3-32 chars: letters, digits, '-' or '_'")
            item = ShortUrl(code=alias, url=url)
            if not self._repo.add(item):
                raise AliasTakenError(f"Alias '{alias}' is already in use")
            return item

        for _ in range(self._max_retries):
            item = ShortUrl(code=self._code_factory(self._code_length), url=url)
            if self._repo.add(item):
                return item
        raise CodeGenerationError("Could not generate a unique code; try again")

    def resolve(self, code: str) -> ShortUrl:
        item = self._repo.get(code)
        if item is None:
            raise CodeNotFoundError(code)
        self._repo.increment_hits(code)
        return item

    def stats(self, code: str) -> ShortUrl:
        item = self._repo.get(code)
        if item is None:
            raise CodeNotFoundError(code)
        return item
