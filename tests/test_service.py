import pytest

from src.shortener.service import (
    AliasTakenError,
    CodeGenerationError,
    CodeNotFoundError,
    InvalidAliasError,
    InvalidUrlError,
    ShortenerService,
    validate_url,
)
from src.shortener.storage import InMemoryRepository


@pytest.fixture
def svc():
    return ShortenerService(InMemoryRepository())


@pytest.mark.parametrize("url", ["https://example.com", "http://a.b/c?d=1"])
def test_validate_url_accepts_http_and_https(url):
    assert validate_url(url) == url


@pytest.mark.parametrize("url", ["", "ftp://x.com", "example.com", "https://", "https://" + "a" * 2050])
def test_validate_url_rejects_bad_input(url):
    with pytest.raises(InvalidUrlError):
        validate_url(url)


def test_shorten_generates_code_of_expected_length(svc):
    item = svc.shorten("https://example.com")
    assert len(item.code) == 7
    assert item.url == "https://example.com"


def test_shorten_with_alias(svc):
    item = svc.shorten("https://example.com", alias="my-link")
    assert item.code == "my-link"


def test_duplicate_alias_rejected(svc):
    svc.shorten("https://example.com", alias="taken")
    with pytest.raises(AliasTakenError):
        svc.shorten("https://other.com", alias="taken")


@pytest.mark.parametrize("alias", ["ab", "has space", "x" * 33, "bad/char"])
def test_invalid_alias_rejected(svc, alias):
    with pytest.raises(InvalidAliasError):
        svc.shorten("https://example.com", alias=alias)


def test_collision_retry_then_success():
    codes = iter(["dup", "dup", "fresh"])
    svc = ShortenerService(InMemoryRepository(), code_factory=lambda n: next(codes))
    assert svc.shorten("https://a.com").code == "dup"
    assert svc.shorten("https://b.com").code == "fresh"


def test_collision_retries_exhausted():
    svc = ShortenerService(InMemoryRepository(), max_retries=3, code_factory=lambda n: "same")
    svc.shorten("https://a.com")
    with pytest.raises(CodeGenerationError):
        svc.shorten("https://b.com")


def test_resolve_increments_hits(svc):
    item = svc.shorten("https://example.com")
    svc.resolve(item.code)
    svc.resolve(item.code)
    assert svc.stats(item.code).hits == 2


def test_resolve_unknown_code(svc):
    with pytest.raises(CodeNotFoundError):
        svc.resolve("nope")
