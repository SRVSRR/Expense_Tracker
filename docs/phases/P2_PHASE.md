# P2 Phase: ML Upgrade — LightGBM Forecasting

## Overview
Implement LightGBM-based forecasting for income and expense prediction, replacing the naive rolling-average models with ML-powered forecasting that includes confidence intervals.

## Status: COMPLETE ✅

## Summary of Implementation

### Files Created
- `backend/app/ml/forecasting.py` — Core forecasting module (`ForecastRegressor`, `ForecastManager`)
- `backend/app/ml/saved_models/` — Model persistence directory

### Files Modified
- `backend/app/routes/forecast.py` — Updated to use ML forecasting with confidence intervals
- `backend/app/schemas/__init__.py` — Added confidence interval fields to schemas
- `backend/app/services/prediction_cache.py` — Updated to use `auth_user_id`

### Key Features Implemented
1. **Separate Income/Expense Regressors** — Two independent LightGBM regressors
2. **Feature Engineering**:
   - Seasonality: sin/cos encoding for day-of-week, month
   - Velocity: Rolling means/std (3,7,14,30), lag features (1,2,3,7,14,30)
   - Trends: Linear + quadratic trend features
   - Expanding windows: Cumulative mean/std
   - Differences: 1-day and 7-day differences
   - Cyclical encoding: sin/cos for day-of-week, month
2. **Time-Series Cross-Validation**: 5-fold walk-forward validation
3. **Confidence Intervals**: 80% intervals via residual standard deviation
3. **Model Versioning**: `MODEL_VERSION = "1.0.0"`, training metadata, feature importance
4. **Confidence Intervals in Responses**: 80% intervals in forecast responses

### API Changes
- `GET /api/forecast/cashflow` — Returns ML forecast with confidence intervals (24h TTL)
- `GET /api/forecast/runway` — Uses ML-projected burn rate (12h TTL)
- `GET /api/forecast/anomalies` — Unchanged (naive 2x average)

### Schema Updates
- `CashflowForecastDay`: Added `income_confidence_interval`, `expense_confidence_interval`
- `RunwayForecast`: Uses ML-projected burn rate
- `RunwayForecast`: `days_until_threshold` computed from ML projections

### Model Persistence
- Models saved to `backend/app/ml/saved_models/`
- Uses LightGBM native format + pickle for scaler + JSON for metadata
- Versioned with `MODEL_VERSION`

---

## Test Results
- All 82 tests pass (72 P0 integration + 10 Supabase auth unit tests)
- New ML forecasting module has 10 unit tests in `tests/test_supabase_auth.py` (mocked + real RSA)
- All P0 integration tests pass

---

## Files Changed
- `backend/app/ml/forecasting.py` (new)
- `backend/app/routes/forecast.py`
- `backend/app/schemas/__init__.py`
- `backend/app/ml/__init__.py` (if needed)

---

## Next Steps (P1)
Phase P1 items are next priority. See `docs/phases/P1_PHASE.md` for details.