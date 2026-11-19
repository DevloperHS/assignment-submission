# Architecture

## Layers

```
HTTP (FastAPI routes)  ->  src/shortener/main.py
        |
        v
Service (business logic)  ->  src/shortener/service.py
        |
        v
Repository interface  ->  src/shortener/storage.py  (UrlRepository protocol)
        |
        v
InMemoryRepository (default)  |  RedisRepository / PostgresRepository (future)
```

- **Routes** handle only HTTP concerns: parsing the request, mapping status codes and building responses.
- **Service** holds the domain rules: code generation, alias validation, collision retries and hit counting. It doesn't import FastAPI or any storage implementation.
- **Repository** is a `Protocol`, and the service receives it through its constructor (dependency injection). Tests use the in-memory implementation.
- **Analytics** (`analytics.py`) is a side-channel client that forwards redirect events to an external service.

Dependencies point inward: routes -> service -> repository interface. Infrastructure is injected.

## Data Model

| Field        | Type     | Notes                            |
|--------------|----------|----------------------------------|
| code         | str (PK) | 7-char base62, or custom alias   |
| url          | str      | validated http/https URL         |
| created_at   | datetime | UTC                              |
| hits         | int      | incremented on each redirect     |

In Postgres, `code` would be the primary key. A unique index on `url` is optional and would let us dedupe repeated URLs.

## Scaling Plan

1. **Stateless API**: run N replicas behind a load balancer.
2. **Storage**: Postgres as the source of truth, with Redis as a read-through cache for `code -> url` (the hot path).
3. **Hit counting**: increment in Redis and flush to Postgres in batches, so we don't write on every redirect.
4. **Code generation**: random base62 with collision retry is fine below about 10^9 rows. Beyond that, switch to a pre-allocated ID range per instance, encoded as base62.
5. **Analytics**: move to a queue (SQS or Kafka) so redirects never wait on a third party.

## Trade-offs

- I used random codes instead of hashing so the same URL can get several distinct codes, for example for per-campaign tracking.
- 307 instead of 301, so browsers don't cache the redirect and hit counts stay accurate.
