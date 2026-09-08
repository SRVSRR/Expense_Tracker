# P1 Phase: Finish Documented Functionality

## Overview
Complete the documented but not-yet-implemented functionality in the API. This phase focuses on finishing features that are documented but not yet implemented, improving API contracts, and adding missing OpenAPI examples.

## Scope
- Recurring transaction contract and auto-creation logic
- Pydantic validation for recurring patterns
- Error handling and rollback for migrations/DB failures
- Cache documentation reconciliation
- App factory/main.py alignment
- OpenAPI examples for all endpoints

## Success Criteria
- All P1 checklist items in TODO.md marked complete
- All endpoints have OpenAPI examples
- Recurring transactions work end-to-end
- Migration error handling is robust
- Cache documentation matches implementation

---

## Tasks

### 1. Recurring Transaction Contract & Auto-Creation
**Status**: Not Started  
**Priority**: High

**Requirements:**
- Define request/response schema for recurring transactions
- Add `is_recurring` flag to transaction create/update
- Auto-create recurring rule when transaction is marked recurring
- Link recurring rule to source transaction

**Files to modify:**
- `backend/app/schemas/__init__.py` - Add recurring transaction schemas
- `backend/app/routes/transactions.py` - Add auto-creation logic
- `backend/app/routes/recurring.py` - Ensure compatibility
- `backend/tests/test_crud_integration.py` - Add tests

**Acceptance Criteria:**
- POST `/api/transactions/` with `is_recurring=true` + `recurring_pattern` creates transaction + recurring rule
- GET `/api/transactions/{id}` returns recurring rule info if linked
- Recurring rule has `transaction_id` pointing to source transaction

---

### 2. Pydantic Constraints for Recurring Patterns
**Status**: Not Started  
**Priority**: High

**Requirements:**
- Validate `pattern` enum: `daily`, `weekly`, `biweekly`, `monthly`, `quarterly`, `yearly`
- Validate `frequency` positive integer (>=1)
- Validate `expected_date` is future date
- Validate `expected_amount` positive float

**Files to modify:**
- `backend/app/schemas/__init__.py` - Add constraints to `RecurringRuleCreate`
- `backend/app/routes/recurring.py` - Add validation error handling

**Acceptance Criteria:**
- Invalid pattern returns 422 with clear error
- Frequency < 1 returns 422
- Past `expected_date` returns 422

---

### 3. Error Handling & Rollback for Migrations/DB Failures
**Status**: Not Started  
**Priority**: Medium

**Requirements:**
- Wrap migration operations in transactions with rollback on failure
- Add retry logic for transient DB errors
- Implement circuit breaker for external services (Supabase)
- Add structured error responses with error codes

**Files to modify:**
- `backend/alembic/env.py` - Transaction wrapping
- `backend/app/utils/__init__.py` - Retry decorator
- `backend/app/utils/__init__.py` - Circuit breaker
- `backend/app/utils/exceptions.py` - Custom exception classes (new file)
- `backend/app/routes/*` - Use custom exceptions

**Acceptance Criteria:**
- Failed migration rolls back cleanly
- Transient DB errors retry 3x with exponential backoff
- Supabase outage returns 503 with retry-after header
- All errors have consistent format: `{code, message, details}`

---

### 4. Cache Documentation Reconciliation
**Status**: Not Started  
**Priority**: Medium

**Requirements:**
- Document `budget_analysis` cache type in code and docs
- Document all cache types with TTLs in one place
- Add cache invalidation triggers documentation

**Files to modify:**
- `backend/app/services/prediction_cache.py` - Docstring with all cache types
- `docs/INFRASTRUCTURE.md` - Update cache section
- `docs/phases/CACHE_STRATEGY.md` - New file (create)

**Cache Types to Document:**
| Type | TTL | Invalidation Triggers |
|------|-----|----------------------|
| cashflow | 24h | Transaction create/update/delete, Account create/update/delete, Recurring create/delete |
| runway | 12h | Same as cashflow |
| anomaly | 24h | Transaction create/update/delete |
| budget | 7d | Transaction create/update/delete, Account create/update/delete, Recurring create/delete |
| budget_analysis | 7d | Same as budget |

---

### 5. App Factory / main.py Alignment
**Status**: Not Started  
**Priority**: Medium

**Requirements:**
- Extract app creation to `backend/app/factory.py`
- `main.py` imports from factory
- Both use same router registration and lifespan
- Lifespan handles migrations consistently

**Files to modify:**
- `backend/app/factory.py` (new file)
- `backend/main.py` - Import from factory
- `backend/app/routes/__init__.py` - Ensure all routers exported

**Acceptance Criteria:**
- `uvicorn main:app --reload` works
- Tests can import `create_app()` from factory
- No duplicate router registration

---

### 6. OpenAPI Examples for All Endpoints
**Status**: Partially Done (forecast done)  
**Priority**: Medium

**Requirements:**
- Add request/response examples to all route schemas
- Include error response examples (400, 401, 404, 422, 500)
- Use realistic data matching seed categories

**Endpoints needing examples:**
- `/api/accounts/*` - All CRUD
- `/api/transactions/*` - All CRUD + filters
- `/api/categories/*` - All CRUD + parent hierarchy
- `/api/recurring/*` - CRUD + upcoming
- `/api/budget/*` - Recommendations + category analysis
- `/api/categorize/*` - Suggest, corrections, train, model-info

**Files to modify:**
- `backend/app/schemas/__init__.py` - Add `json_schema_extra` to all schemas
- `backend/app/routes/*` - Add `response_description` and `responses` to route decorators

**Acceptance Criteria:**
- `/docs` shows request/response examples for all endpoints
- Error responses documented with examples
- Examples use realistic data (seed categories, realistic amounts)

---

## Dependencies
- P0: Complete ✅
- P2 (ML Upgrade): Complete ✅
- Auth Migration: Complete ✅

## Timeline Estimate
| Task | Estimate |
|------|----------|
| 1. Recurring Contract | 2-3 days |
| 2. Pydantic Constraints | 1 day |
| 3. Error Handling | 2-3 days |
| 4. Cache Docs | 1 day |
| 5. Factory Alignment | 1 day |
| 6. OpenAPI Examples | 2-3 days |
| **Total** | **9-12 days** |

## Definition of Done
- [ ] All P1 tasks complete
- [ ] All P1 tests pass
- [ ] Documentation updated
- [ ] OpenAPI examples visible in `/docs`
- [ ] TODO.md updated with checkmarks