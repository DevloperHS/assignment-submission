# URL Shortener API — Take-Home Submission

Candidate: Raghuveer

A small REST API that shortens long URLs and redirects short codes back to the original URL. Built with FastAPI.

## Features

- `POST /urls`: create a short code for a URL (with an optional custom alias)
- `GET /{code}`: redirect (307) to the original URL
- `GET /urls/{code}/stats`: see the hit count and creation time
- Input validation for URLs and aliases
- Pluggable storage. In-memory by default; the repository interface makes it easy to add Redis or Postgres.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn src.shortener.main:app --reload
```

Then open http://127.0.0.1:8000/docs for the interactive OpenAPI docs.

## Test

```bash
pytest -q
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/some/very/long/path"}'
# {"code":"aZ3kQ9x","short_url":"http://127.0.0.1:8000/aZ3kQ9x","url":"https://example.com/some/very/long/path"}
```

## Notes / Trade-offs

- I used in-memory storage to keep the submission self-contained. See ARCHITECTURE.md for how it would scale.
- Analytics events go to a third-party analytics service. I didn't have time to make this async.
