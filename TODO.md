# Expense Tracker Delivery Checklist

Status: API foundation exists; correctness and operational work is in progress.

## P0 - Make the current API trustworthy

- [x] Keep account balances consistent when transactions are created, updated, or deleted.
- [x] Reject recurring rules that reference another user's transaction.
- [x] Invalidate derived predictions after account and recurring-rule mutations.
- [ ] Add integration tests for registration, login, auth failures, and user isolation.
- [ ] Add integration tests for account, transaction, category, and recurring CRUD.
- [ ] Add integration tests for forecast, budget, and cache invalidation behavior.
- [ ] Validate category ownership when creating or updating `parent_id`.
- [ ] Decide whether transaction edits may change type/account; if supported, update both affected balances atomically.

## P1 - Finish documented functionality

- [ ] Define the recurring transaction request contract and automatically create a recurring rule when a transaction is marked recurring.
- [ ] Validate recurring patterns and positive frequencies with Pydantic constraints.
- [ ] Add explicit error handling and rollback behavior around migration and database failures.
- [ ] Reconcile the cache documentation with the implemented `budget_analysis` cache type.
- [ ] Make the app factory and `main.py` use the same router and lifespan configuration.
- [ ] Add OpenAPI examples and response schemas for forecast, budget, recurring, and categorization endpoints.

## P2 - ML upgrade

- [ ] Add separate LightGBM income and expense regressors.
- [ ] Add seasonality, spend velocity, and other documented features.
- [ ] Add scheduled prediction generation and cache writes.
- [ ] Add confidence ranges to forecast responses.
- [ ] Add model versioning and reproducible training metadata.

## P3 - Production hardening

- [ ] Move authentication to Supabase Auth or document the decision to retain local JWT.
- [ ] Use a strong production `SECRET_KEY` and environment-specific CORS origins.
- [ ] Add rate limiting, structured logs, backups, and error monitoring.
- [ ] Run migrations as a release step and add a health check that verifies database connectivity.
- [ ] Deploy the API and configure a stable HTTPS URL for mobile and desktop clients.
- [ ] Add CI for tests, syntax checks, and dependency/security scanning.

## Definition of done

- All P0 items pass in CI.
- Every documented endpoint has an integration test for its happy path and auth/user-isolation behavior.
- The API starts from a clean database using migrations.
- A deployed environment can be configured from documented environment variables only.
