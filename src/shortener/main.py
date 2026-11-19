"""HTTP layer: FastAPI routes."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from . import analytics, config
from .service import (
    AliasTakenError,
    CodeGenerationError,
    CodeNotFoundError,
    InvalidAliasError,
    InvalidUrlError,
    ShortenerService,
)
from .storage import InMemoryRepository

app = FastAPI(title="URL Shortener", version="1.0.0")

_service = ShortenerService(
    InMemoryRepository(),
    code_length=config.CODE_LENGTH,
    max_retries=config.MAX_COLLISION_RETRIES,
)


def get_service() -> ShortenerService:
    return _service


class CreateUrlRequest(BaseModel):
    url: str = Field(..., max_length=2048, examples=["https://example.com/long/path"])
    alias: Optional[str] = Field(None, examples=["my-link"])


class CreateUrlResponse(BaseModel):
    code: str
    short_url: str
    url: str


class StatsResponse(BaseModel):
    code: str
    url: str
    hits: int
    created_at: datetime


@app.post("/urls", response_model=CreateUrlResponse, status_code=status.HTTP_201_CREATED)
def create_url(body: CreateUrlRequest, svc: ShortenerService = Depends(get_service)):
    try:
        item = svc.shorten(body.url, body.alias)
    except (InvalidUrlError, InvalidAliasError) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except AliasTakenError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    except CodeGenerationError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    return CreateUrlResponse(code=item.code, short_url=f"{config.BASE_URL}/{item.code}", url=item.url)


@app.get("/urls/{code}/stats", response_model=StatsResponse)
def get_stats(code: str, svc: ShortenerService = Depends(get_service)):
    try:
        item = svc.stats(code)
    except CodeNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Short code not found")
    return StatsResponse(code=item.code, url=item.url, hits=item.hits, created_at=item.created_at)


@app.get("/{code}")
def redirect(code: str, request: Request, svc: ShortenerService = Depends(get_service)):
    try:
        item = svc.resolve(code)
    except CodeNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Short code not found")
    analytics.track_redirect(code, request.headers.get("user-agent"), request.headers.get("referer"))
    return RedirectResponse(item.url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
