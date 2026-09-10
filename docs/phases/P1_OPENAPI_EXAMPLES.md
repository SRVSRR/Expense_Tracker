# P1: OpenAPI Examples & Response Schemas

## Objective
Add comprehensive OpenAPI examples and response schemas for all endpoints in forecast, budget, recurring, and categorize routers to improve developer experience in Swagger UI (`/docs`) and ReDoc (`/redoc`).

## Current State
- ✅ Forecast endpoints have basic schemas (`CashflowForecast`, `RunwayForecast`, `AnomaliesResponse`)
- ✅ Budget has basic schemas (`BudgetRecommendations`, `CategoryAnalysis`)
- ✅ Recurring has basic schemas (`RecurringRule`, `RecurringUpcomingItem`)
- ✅ Categorize has basic schemas (`CategorizeSuggestResponse`, `CategorizeTrainResponse`, `CategorizeModelInfo`)
- ❌ Most endpoints lack `json_schema_extra` examples
- ❌ No request body examples for POST/PUT endpoints
- ❌ No error response examples (400, 401, 404, 422)
- ❌ No response headers documented

---

## Plan

### Phase 1: Schema-Level Examples (`backend/app/schemas/__init__.py`)

#### 1.1 Recurring Schemas
- `RecurringRuleCreate` - Add request example
- `RecurringRule` - Add response example with all fields
- `RecurringUpcomingItem` - Already has example ✅

#### 1.2 Forecast Schemas
- `CashflowForecastDay` - Already has example ✅ (added confidence intervals)
- `CashflowForecast` - Already has example ✅
- `RunwayForecast` - Already has example ✅
- `AnomaliesResponse` / `AnomalyItem` - Has example ✅

#### 1.3 Budget Schemas
- `BudgetRecommendationItem` - Add example
- `BudgetRecommendations` - Has example ✅
- `CategoryAnalysisItem` - Add example
- `CategoryAnalysis` - Has example ✅

#### 1.4 Categorize Schemas
- `CategorizeSuggestRequest` - Add example
- `CategorizeSuggestResponse` - Has example ✅
- `CategorizeCorrectionRequest` - Add example
- `CategorizeTrainResponse` - Has example ✅
- `CategorizeModelInfo` - Has example ✅

#### 1.5 Transaction/Account/Category Schemas (if missing)
- Verify all have examples

---

### Phase 2: Route-Level Examples (`backend/app/routes/*.py`)

#### 2.1 Forecast Routes (`forecast.py`)
- `GET /cashflow` - Add response examples (200, 401, 422)
- `GET /runway` - Add response examples
- `GET /anomalies` - Add response examples

#### 2.2 Budget Routes (`budget.py`)
- `GET /recommendations` - Add response examples
- `GET /category-analysis` - Add response examples

#### 2.3 Recurring Routes (`recurring.py`)
- `POST /recurring/` - Request body example, 201/400/401/404/422
- `GET /recurring/` - Response example
- `GET /recurring/upcoming` - Response example
- `DELETE /recurring/{rule_id}` - 204/401/404

#### 2.4 Categorize Routes (`categorize.py`)
- `POST /suggest` - Request/response examples
- `POST /corrections` - Request/response examples
- `POST /train` - Response examples (success, no_data, error)
- `GET /model-info` - Response example

#### 2.2-2.5 Account/Transaction/Category Routes
- Add examples to all CRUD endpoints

---

### Phase 3: Error Response Examples

Add standard error response examples to all routes:
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found
- 422 Validation Error
- 429 Rate Limited
- 500 Internal Server Error

---

## Implementation Order

1. **Schema examples first** (`schemas/__init__.py`) - Foundation for route docs
2. **Route-level examples** (each router file)
3. **Error response documentation** (global + per-route)

---

## Validation

After implementation:
1. Run tests: `pytest tests/ --tb=no -q`
2. Verify `/docs` shows examples for all endpoints
4. Verify `/redoc` renders correctly
5. Check OpenAPI JSON: `GET /openapi.json`

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/schemas/__init__.py` | Add `json_schema_extra` to all missing schemas |
| `backend/app/routes/forecast.py` | Add route examples |
| `backend/app/routes/budget.py` | Add route examples |
| `backend/app/routes/recurring.py` | Add route examples |
| `backend/app/routes/categorize.py` | Add route examples |
| `backend/app/routes/accounts.py` | Add examples (if missing) |
| `backend/app/routes/transactions.py` | Add examples (if missing) |
| `backend/app/routes/categories.py` | Add examples (if missing) |
| `backend/app/routes/categorize.py` | Add route examples |
| `backend/app/routes/auth.py` | Error response examples |

---

## Example Template

### Request Body Example
```python
class RecurringRuleCreate(RecurringRuleBase):
    transaction_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 1500.00,
                "expected_date": "2026-10-01T00:00:00",
                "transaction_id": "txn_abc123"
            }
        }
```

### Response Example
```python
class RecurringRule(RecurringRuleBase):
    id: str
    auth_user_id: str
    transaction_id: Optional[str] = None
    last_matched: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rule_abc123",
                "auth_user_id": "user_123",
                "transaction_id": "txn_abc123",
                "pattern": "monthly",
                "frequency": 1,
                "expected_amount": 1500.00,
                "expected_date": "2026-10-01T00:00:00",
                "last_matched": None,
                "created_at": "2026-09-07T10:30:00"
            }
        }
```

### Error Response Example (in route)
```python
@router.post(
    "/",
    response_model=RecurringRule,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Recurring rule created successfully"},
        400: {"description": "Invalid input", "model": ErrorResponse, "content": {"application/json": {"example": {"error": {"code": "VALIDATION_ERROR", "message": "Invalid recurring pattern", "details": {"field": "pattern"}}}}}},
        401: {"description": "Unauthorized"},
        404: {"description": "Transaction not found"},
        422: {"description": "Validation error"},
    },
)
```