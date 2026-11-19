import pytest
from fastapi.testclient import TestClient

from src.shortener import analytics
from src.shortener.main import app, get_service
from src.shortener.service import ShortenerService
from src.shortener.storage import InMemoryRepository


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(analytics, "track_redirect", lambda *a, **k: None)
    svc = ShortenerService(InMemoryRepository())
    app.dependency_overrides[get_service] = lambda: svc
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_and_redirect(client):
    r = client.post("/urls", json={"url": "https://example.com/page"})
    assert r.status_code == 201
    code = r.json()["code"]

    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "https://example.com/page"


def test_stats_counts_hits(client):
    code = client.post("/urls", json={"url": "https://example.com"}).json()["code"]
    client.get(f"/{code}", follow_redirects=False)
    r = client.get(f"/urls/{code}/stats")
    assert r.status_code == 200
    assert r.json()["hits"] == 1


def test_invalid_url_returns_422(client):
    r = client.post("/urls", json={"url": "not-a-url"})
    assert r.status_code == 422


def test_alias_conflict_returns_409(client):
    client.post("/urls", json={"url": "https://a.com", "alias": "promo"})
    r = client.post("/urls", json={"url": "https://b.com", "alias": "promo"})
    assert r.status_code == 409


def test_unknown_code_returns_404(client):
    assert client.get("/missing", follow_redirects=False).status_code == 404
    assert client.get("/urls/missing/stats").status_code == 404
