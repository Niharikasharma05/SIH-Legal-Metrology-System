# SetuCheck

## Local infrastructure (Phase 1)

This stack provides persistent PostgreSQL and MinIO services plus the existing
FastAPI application and a placeholder worker. OCR remains synchronous in the
current endpoint until Phase 2; no authentication, reports, or frontend work
is included here.

### Start

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:8000/health
docker compose exec api python scripts/smoke_infra.py
```

The API is at `http://localhost:8000`; MinIO Console is at
`http://localhost:9001`. The API runs `alembic upgrade head` at startup, so
the schema is always created from the migration files.

### Persistence check

```bash
docker compose down
docker compose up -d
docker compose exec api python scripts/smoke_infra.py
```

Named `postgres_data` and `minio_data` volumes preserve records and objects
across this restart. Do not use `docker compose down -v` unless you intend to
delete the local database and object store.

### Storage boundary

`storage.py` stores object keys rather than public object URLs. The local
bucket is provisioned only when `APP_ENV` is `development`, `test`, or
`local`; non-local deployments must provision storage explicitly.
