# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing **security@expense-tracker.example.com** (replace with actual contact).

Do not open public issues for security vulnerabilities. We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Security Measures

### Authentication
- JWT tokens with HS256 algorithm
- Tokens expire after 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Passwords hashed with bcrypt (cost factor 12)
- Tokens transmitted only over HTTPS in production

### Authorization
- All API endpoints require valid JWT bearer token
- User-scoped queries: every database query filters by `user_id`
- Cross-user access attempts return 404 (not 403) to avoid user enumeration

### Data Protection
- No sensitive data in logs (passwords, tokens filtered)
- SQLite dev database excluded from version control
- Production uses PostgreSQL via Supabase with TLS
- Environment variables for secrets (`SECRET_KEY`, `DATABASE_URL`)

### API Security
- CORS configured for development (`allow_origins=["*"]`) — restrict in production
- Input validation via Pydantic schemas on all endpoints
- SQL injection prevention via SQLAlchemy ORM (parameterized queries)
- Rate limiting: not yet implemented (planned for P3)

### Dependencies
- `bcrypt` pinned to `<5` (v4.x compatible, v5.x breaks passlib)
- Regular dependency updates via `pip-audit` / Dependabot (planned for CI)

## Production Checklist

Before deploying to production:

- [ ] Generate strong `SECRET_KEY` (32+ random bytes)
- [ ] Set `CORS_ORIGINS` to specific frontend domains
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
| Brute force | Not yet implemented (planned: rate limit /account lockout) |
| Weak passwords | Min 6 chars enforced, bcrypt hashing |
| Secret exposure | `.env` in `.gitignore`, production secrets in vault |

## Security-Related Configuration

```env
# .env (development only)
DATABASE_URL=sqlite+aiosqlite:///./expense_tracker.db
SECRET_KEY=dev-secret-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Production should override all values and use a managed secrets store.