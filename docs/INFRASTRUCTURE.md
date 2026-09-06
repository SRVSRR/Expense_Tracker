# Infrastructure and API Operations

## Local development

Requirements: Python 3.13, a virtual environment, and a database URL.

```sh
cd backend
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. OpenAPI is at `/docs`, `/redoc`, and `/openapi.json`. Run tests with:

```sh
pytest -q
```

The local `.env` should use the Supabase Transaction pooler:

```env
DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<password>@<pooler-host>:6543/postgres
SECRET_KEY=replace-with-a-long-random-development-value
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

The API startup runs Alembic migrations against Supabase. Do not commit `.env` or expose the database URL.

## Supabase/PostgreSQL

1. Create a Supabase project and copy its pooled PostgreSQL connection string.
2. For the Supabase **Transaction pooler**, select port `6543` in the Connect panel and store the resulting string in the local secret file `backend/.env` as `DATABASE_URL`. Convert the driver prefix to `postgresql+asyncpg://` if Supabase provides `postgres://` or `postgresql://`.
3. The application automatically sets `asyncpg`'s `statement_cache_size=0` for PostgreSQL URLs, which is required when using transaction pooling. Do not put the password in source control, logs, or client applications.
4. Set a unique production `SECRET_KEY`.
5. Run migrations from the backend directory before starting the service:

```sh
alembic upgrade head
```

6. Confirm `/health`, `/docs`, registration, login, and a protected endpoint.

The current API uses local JWT authentication. Supabase can provide PostgreSQL immediately, but switching identity to Supabase Auth is a separate migration and requires client token changes.

## Hosting

Railway or Render are suitable for the API. Configure a Python service with:

- Build command: `pip install -r backend/requirements.txt`
- Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health path: `/health`
- Environment variables: `DATABASE_URL`, `SECRET_KEY`, and `ACCESS_TOKEN_EXPIRE_MINUTES`

Use the provider's managed HTTPS URL as the client base URL. Set production CORS to the actual mobile/web client origins instead of `*` when browser clients are introduced. Never expose the database URL or JWT secret to mobile or desktop clients.

## Client connection

Clients call the deployed base URL with the `/api` prefix, for example:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/accounts/`
- `GET /api/transactions/`

After login, send `Authorization: Bearer <access_token>` on every protected request. Store the token using the platform's secure storage. On HTTP 401, clear the token and return the user to login.

## Release checklist

- Provision PostgreSQL and verify backups.
- Set secrets in the hosting provider, not in source control.
- Run `alembic upgrade head`.
- Deploy and check `/health` and `/docs`.
- Register a test user and exercise account and transaction CRUD.
- Verify a second user cannot read or mutate the first user's data.
- Configure logs, uptime monitoring, and error tracking.
- Record the deployed API URL in each client repository's environment configuration.
