# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing **your-personal-email@example.com** (replace with actual contact).

Do not open public issues for security vulnerabilities. We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Security Measures

### Authentication
- JWT tokens with RS256 algorithm (verified via Supabase JWKS)
- Tokens issued and managed by Supabase Auth
- Supabase handles password hashing (bcrypt), token issuance, and refresh
- Tokens transmitted only over HTTPS in production
- JWT secret rotation handled by Supabase (automatic key rotation)

### Authorization
- All API endpoints require valid JWT bearer token (Supabase-issued)
- User-scoped queries: every database query filters by `auth_user_id`
- Cross-user access attempts return 404 (not 403) to avoid user enumeration

### Data Protection
- No sensitive data in logs (passwords, tokens filtered)
- SQLite dev database excluded from version control
- Production uses PostgreSQL via Supabase with TLS
- Environment variables for secrets (`SUPABASE_JWKS_URL`, `SUPABASE_ISSUER`, `DATABASE_URL`)
- Supabase transaction-pooler connections disable asyncpg prepared-statement caching; database credentials remain local or in the hosting provider's secret store

### API Security
- CORS loaded from `CORS_ORIGINS` env var (comma-separated allowlist). Outside tests, wildcards are rejected and a missing value fails startup — no permissive CORS in production.
- Input validation via Pydantic schemas on all endpoints
- SQL injection prevention via SQLAlchemy ORM (parameterized queries)
- Rate limiting: partially implemented with `slowapi`; ML training is limited to 2 requests/hour. Broader production limits and monitoring remain planned for P3.

### Email Enumeration
**Supabase Auth handles registration**: Supabase's signup flow uses email verification and does not expose whether an email exists in the same way as a custom registration endpoint. The email enumeration trade-off from the previous local auth implementation no longer applies.

### Password Policy
**Managed by Supabase Auth**: Supabase enforces secure password policies (minimum 8 characters by default, configurable). Local password handling has been removed; all authentication is delegated to Supabase Auth.

### ML Model Artifact Safety
LightGBM models are saved to `backend/app/ml/saved_models/` via `joblib.dump`/`joblib.load` (not raw pickle). Model files are **only loaded from trusted, backend-controlled storage** — no user input influences the model path, and the directory is not writable by the web process in production. Treat model artifacts as code: do not accept model files from untrusted sources.

### Dependencies
- `bcrypt` pinned to `<5` (v4.x compatible, v5.x breaks passlib) — still used for test fixtures
- Regular dependency updates via `pip-audit` / Dependabot (planned for CI)

## Production Checklist

Before deploying to production:

- [ ] Set `SUPABASE_JWKS_URL` and `SUPABASE_ISSUER` environment variables
- [x] Set `CORS_ORIGINS` to specific frontend domains (wildcards rejected, missing value fails startup outside tests)
- [ ] Enable HTTPS/TLS termination
- [ ] Configure PostgreSQL with SSL mode (Supabase Transaction Pooler)
- [ ] Set up structured logging and monitoring
- [ ] Enable rate limiting (e.g., slowapi)
- [ ] Run `pip-audit` on dependencies
- [ ] Configure backup and point-in-time recovery for database

## Threat Model

| Threat | Mitigation |
|--------|------------|
| Token theft | Short expiry, HTTPS only, secure storage on clients |
| SQL injection | SQLAlchemy ORM, no raw SQL |
| User data leakage | All queries scoped by `auth_user_id`, 404 for foreign resources |
| Brute force | Supabase Auth handles rate limiting and account protection |
| Weak passwords | Supabase Auth enforces password policies |
| Secret exposure | `.env` in `.gitignore`, production secrets in vault |
| ML model RCE | Models loaded only from trusted backend storage (see [ML Model Artifact Safety](#ml-model-artifact-safety)) |
| Email enumeration | Supabase Auth handles registration flow securely |

## Security-Related Configuration

```env
# .env (development only)
DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<password>@<pooler-host>:6543/postgres
SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_ISSUER=https://<project-ref>.supabase.co/auth/v1
SECRET_KEY=dev-secret-change-in-production  # only used for test tokens
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

For Supabase Transaction pooler connections, use the port-6543 `postgresql+asyncpg://` URL in `DATABASE_URL`. The application disables prepared statements automatically for this PostgreSQL URL. Never commit or expose the URL because it contains the database password.

Production should override all values and use a managed secrets store.