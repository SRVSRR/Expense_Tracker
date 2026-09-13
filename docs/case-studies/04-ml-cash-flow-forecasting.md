# Forecasting Cash Flow with Uncertainty, Not Just Averages

**Reading time:** 8 minutes  
**Audience:** Data science, machine learning engineering, and hiring managers  
**Repository evidence:** `backend/app/ml/forecasting.py`, `backend/app/routes/forecast.py`, `backend/app/services/prediction_cache.py`

## Problem

Simple finance forecasts usually report one number per day: expected income minus expected expenses. That hides the most important question for a user: how uncertain is the projection?

A rolling average also ignores weekly behavior, monthly cycles, recent spending velocity, and the very different statistical behavior of income versus expenses. Combining income and expenses into one net series too early can wash out useful signal.

The goal was to produce useful projections while making uncertainty explicit. A second goal was to keep forecasts reproducible: the same history plus the same model version should imply the same methodology, even if individual predictions change as new data arrives. For data-engineering interviews, the companion discipline is equally important—user-scoped caching, mutation-driven invalidation, and versioned response schemas around the models.

## Approach

I implemented separate LightGBM regressors for income and expense forecasting.

### 1. Separate the two forecasting problems

Income and expenses behave differently:

- Income is often periodic and relatively stable.
- Expenses are spikier, category-dependent, and sensitive to weekends or month boundaries.

Training one regressor per series preserves those differences. The cash-flow projection is then derived from the two independent forecasts. Runway is computed from the resulting average income, expenses, net burn, current balance, and threshold.

### 2. Engineer time-aware features

Each daily aggregate is expanded into features intended to capture seasonality, momentum, and trend:

- Calendar features: day of week, day of month, week, month, quarter, weekend and month-boundary indicators.
- Cyclical encodings: sine and cosine representations for weekly and monthly seasonality.
- Rolling statistics: means, spreads, minima, and maxima over 3-, 7-, 14-, and 30-day windows.
- Lag features: 1-, 2-, 3-, 7-, 14-, and 30-day lags.
- Expanding statistics: cumulative mean and spread.
- Short-term differences: one-day and seven-day changes.
- Trend features: linear and quadratic time indices.

This turns raw transaction history into a supervised regression dataset while preserving temporal order.

### 3. Validate like a time series

The models use walk-forward-style cross-validation rather than random train/test splits. Random splits would leak future behavior into training and overstate performance.

Final accuracy is tracked with MAE, RMSE, MAPE, and R². Training metadata records:

- Model version
- Training sample count
- Training date
- Feature names
- Metrics
- Feature importance

The current implementation is versioned as model `1.0.0`.

### 4. Make uncertainty part of the API

Each forecast includes 80% confidence intervals derived from residual variation. The API response therefore carries:

- Projected balance
- Expected income
- Expected expense
- Income confidence interval
- Expense confidence interval

That lets a client distinguish between “likely stable” and “highly variable” projections, rather than treating every forecast as equally reliable. Narrow intervals suggest repeatable history; wide intervals warn that daily outcomes may diverge from the point forecast.

### 5. Cache forecasts responsibly

Forecast generation is request-driven and cached per user in the `predictions` table:

- Cash-flow forecasts: 24 hours
- Runway forecasts: 12 hours
- Anomaly results: 24 hours

Transaction, account, and recurring-rule mutations invalidate the affected user’s cache. There is no background scheduler yet; that remains explicit technical debt rather than a hidden assumption.

## Stack

- LightGBM regression
- pandas time-series aggregation and feature engineering
- scikit-learn scaling and regression metrics
- FastAPI forecast endpoints
- PostgreSQL-backed prediction cache with TTL and invalidation
- Pydantic response schemas with confidence-interval fields

## Results

- `/api/forecast/cashflow` returns ML-powered daily projections with confidence intervals.
- `/api/forecast/runway` derives remaining runway from ML-projected income and expenses.
- `/api/forecast/anomalies` continues to flag expenses exceeding twice their category average.
- Model version, training samples, metrics, and feature importance are persisted for reproducibility.
- Cache behavior remains user-scoped and invalidation-aware.

### 6. Handle sparse and degenerate histories explicitly

A forecasting system must define behavior when data is thin. This implementation does that in several ways:

- Separate models are used only when enough daily samples exist.
- Sparse income or expense histories produce conservative zero-valued components rather than fabricated confidence.
- Runway falls back to an undefined remaining-days value when projected burn is non-positive.
- Forecasts remain scoped to the authenticated user, so one sparse history cannot contaminate another user’s projection.

These rules prevent the model from inventing precision where the underlying ledger offers none. A forecast with no credible history should be visibly conservative, not confidently wrong.

Example forecast day:

```json
{
  "date": "2026-09-08",
  "projected_balance": 5114.5,
  "expected_income": 100.0,
  "expected_expense": 85.5,
  "income_confidence_interval": {
    "lower": 75.0,
    "upper": 125.0
  },
  "expense_confidence_interval": {
    "lower": 60.0,
    "upper": 110.0
  }
}
```

### 7. Make the forecast reviewable end to end

An evaluator can follow the full path without guessing:

1. Read the feature-engineering logic in `ForecastRegressor`.
2. Check training thresholds, version, metrics, and feature importance.
3. Read the cash-flow conversion and runway derivation in the forecast routes.
4. Inspect the confidence-interval fields in the response schemas.
5. Verify cache TTLs and invalidation in the prediction-cache service.
6. Check integration coverage for forecast shape, isolation, cache reuse, expiry, and invalidation.

That trace—from historical transactions to engineered features, model output, confidence interval, cache entry, and API response—is the real deliverable. It also makes future model changes safer: a new version can be compared through the same schemas, caches, tests, and deployment health checks.

## Lessons

1. **Don’t model net cash flow directly at first.** Separate income and expense models preserve fundamentally different behaviors.
2. **Time order matters.** Walk-forward validation is more honest than random splits for forecasting.
3. **Uncertainty is a feature.** Confidence intervals make a forecast actionable instead of merely decorative.
4. **Persist everything needed to reproduce a model.** Version, features, metrics, and training metadata matter as much as the model file.
5. **Be explicit about missing schedulers.** Request-driven caching is a valid architecture, but it should be documented rather than implied.
6. **Keep simple detectors separate.** Rule-based anomaly detection remains useful even after introducing regression forecasting; not every analytical question needs the same model.
