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
- JWT tokens with HS256 algorithm
- Tokens expire after 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Passwords hashed with bcrypt (cost factor 12)
- Tokens transmitted only over HTTPS in production
- **JWT secret rotation**: not yet implemented; rotating `SECRET_KEY` currently invalidates all active sessions

### Authorization
- All API endpoints require valid JWT bearer token
- User-scoped queries: every database query filters by `user_id`
- Cross-user access attempts return 404 (not 403) to avoid user enumeration

### Data Protection
- No sensitive data in logs (passwords, tokens filtered)
- SQLite dev database excluded from version control
- Production uses PostgreSQL via Supabase with TLS
- Environment variables for secrets (`SECRET_KEY`, `DATABASE_URL`)
- Supabase transaction-pooler connections disable asyncpg prepared-statement caching; database credentials remain local or in the hosting provider's secret store

### API Security
- CORS configured for development (`allow_origins=["*"]`) — restrict in production (see Production Checklist)
- Input validation via Pydantic schemas on all endpoints
- SQL injection prevention via SQLAlchemy ORM (parameterized queries)
- Rate limiting: not yet implemented (planned for P3)

### Email Enumeration Trade-off
**Known gap**: `POST /api/auth/register` returns `400 "Email already registered"` when an email exists, which allows account enumeration. This is a deliberate trade-off for UX (immediate feedback vs. "check your email" flow). A future improvement would unify the response and rely on the login/forgot-password flow to confirm existence.

### Password Policy
**Current**: Minimum 6 characters, no complexity requirements.  
**Rationale**: Below NIST SP 800-63B guidance (8+ chars minimum). Chosen for low-friction dev/test onboarding. Production should enforce 8+ characters and check against breach lists (e.g., via `zxcvbn` or HaveIBeenPwned API).

### ML Model Artifact Safety
LightGBM models are saved to `backend/app/ml/saved_models/` via `joblib.dump`/`joblib.load` (not raw pickle). Model files are **only loaded from trusted, backend-controlled storage** — no user input influences the model path, and the directory is not writable by the web process in production. Treat model artifacts as code: do not accept model files from untrusted sources.

### Dependencies
- `bcrypt` pinned to `<5` (v4.x compatible, v5.x breaks passlib)
- Regular dependency updates via `pip-audit` / Dependabot (planned for CI)

## Production Checklist

Before deploying to production:

- [ ] Generate strong `SECRET_KEY` (32+ random bytes)
- [ ] Set `CORS_ORIGINS` to specific frontend domains (see [CORS configuration](#api-security))
- [ ] Enable HTTPS/TLS termination
- [ ] Configure PostgreSQL with SSL mode
- [ ] Set up structured logging and monitoring
- [ ] Enable rate limiting (e.g., slowapi)
- [ ] Run `pip-audit` on dependencies
- [ ] Configure backup and point-in-time recovery for database

## Threat Model

| Threat | Mitigation |
|--------|------------|
| Token theft | Short expiry, HTTPS only, secure storage on clients |
| SQL injection | SQLAlchemy ORM, no raw SQL |
| User data leakage | All queries scoped by `user_id`, 404 for foreign resources |
| Brute force | Not yet implemented (planned: rate limit / account lockout) |
| Weak passwords | Min 6 chars enforced (see [Password Policy](#password-policy)), bcrypt hashing |
| Secret exposure | `.env` in `.gitignore`, production secrets in vault |
| ML model RCE | Models loaded only from trusted backend storage (see [ML Model Artifact Safety](#ml-model-artifact-safety)) |
| Email enumeration | Registration endpoint leaks existence (see [Email Enumeration Trade-off](#email-enumeration-trade-off)) |

## Security-Related Configuration

```env
# .env (development only)
DATABASE_URL=sqlite+aiosqlite:///./expense_tracker.db
SECRET_KEY=dev-secret-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

For Supabase Transaction pooler connections, use the port-6543 `postgresql+asyncpg://` URL in `DATABASE_URL`. The application disables prepared statements automatically for this PostgreSQL URL. Never commit or expose the URL because it contains the database password.

Production should override all values and use a managed secrets store.