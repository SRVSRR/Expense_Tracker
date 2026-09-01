# AGENTS.md

## Purpose

This file tells a coding agent exactly what to build, in what order, and how
to know each step is done. Follow the phases in sequence. Do not start a
phase until the previous phase's "Definition of done" is satisfied. If
something here is ambiguous, stop and ask rather than guessing.

## Project summary

A mobile personal finance app: manual-entry income + expense tracker with an
AI/ML forecasting layer as the core differentiator. No bank account linking —
manual entry only. Similar in spirit to the app Cashew, but adds cash flow
forecasting, runway prediction, anomaly detection, and budget
recommendations, which manual-entry competitors don't have.

The core tracker (accounts, transactions, budgets) is a commodity feature.
The ML layer is the actual product. Prioritize accordingly once past the
foundation phase.

## Current status (as of 2026-09-01)

**Phases 1–4: COMPLETE (naive implementations)**
**Phases 6–9: COMPLETE (rule-based / naive, not ML-model-driven)**
**Phase 5 (ML categorization): NOT STARTED**
**Phase 10 (auto-recurrence): NOT STARTED**

The app is functional end-to-end: auth, accounts, transactions, categories,
naive cash flow forecast, runway prediction, anomaly detection, and budget
recommendations. All "ML" features currently use simple rolling averages and
rule-based logic — no LightGBM models trained yet.

## Tech stack (do not substitute without asking)

| Layer | Choice | Notes |
|---|---|---|
| Mobile frontend | React Native + Expo (SDK 51) | Run via `npx expo start` |
| State management | Zustand | Stores in `frontend/src/store/` |
| UI components | react-native-paper (MD3) | No `@expo/vector-icons` — use custom `Icon` component |
| Navigation | React Navigation 6 | Bottom tabs + native stack |
| Backend | FastAPI (Python 3.13) | Run via `uvicorn main:app --reload` |
| Database (dev) | SQLite via aiosqlite | File: `backend/expense_tracker.db` |
| Database (prod) | PostgreSQL via Supabase | Swap `.env` `DATABASE_URL` |
| Auth | Local JWT (bcrypt + python-jose) | Not Supabase Auth yet |
| ML | LightGBM, scikit-learn, pandas | Installed but not yet integrated |
| Backend venv | `backend/venv/` | Activate: `source venv/bin/activate` |

### Important compatibility notes
- **No `@expo/vector-icons` in Expo Go**: It causes `_ExpoFontLoader.default.getLoadedFonts is not a function` errors. All icons use a custom text-based `Icon` component at `frontend/src/components/Icon.tsx`.
- **No `react-native-vector-icons`**: Native module, incompatible with Expo Go.
- **bcrypt pinned to <5**: `passlib` is removed; we use `bcrypt` directly. Version 4.x works; 5.x broke passlib.
- **Android API URL**: Use `10.0.2.2:8000` (not `localhost`) — handled in `frontend/src/api/client.ts` via `Platform.select()`.

## UI & Design Constraints

**Read this before making ANY frontend changes.** Violating these will break
the visual design.

### Color palette (`frontend/src/theme/colors.ts`)

| Token | Hex | Usage |
|---|---|---|
| `primary` | `#FF6D00` | **Headers only.** Never on buttons, FABs, or card backgrounds. |
| `tertiary` | `#00BFA5` | Accent links ("See All"), secondary highlights, category icons. |
| `background` | `#0D0D0D` | Screen backgrounds (near-black). |
| `surface` | `#161616` | Tab bar background. |
| `surfaceCard` | `#1A1A1A` | Card backgrounds. |
| `surfaceElevated` | `#1E1E1E` | Elevated surfaces (input fields, empty states). |
| `textPrimary` | `#FFFFFF` | Headings, amounts, primary text. |
| `textSecondary` | `#A0A0A0` | Labels, descriptions. |
| `textTertiary` | `#666666` | Hints, metadata, disabled text. |
| `textDisabled` | `#444444` | Placeholder icons, very muted text. |
| `border` | `#2A2A2A` | Card borders, dividers. |
| `income` | `#66BB6A` | Income amounts, positive changes. |
| `expense` | `#EF5350` | Expense amounts, negative changes, errors. |
| `warning` | `#FFA726` | Anomaly warnings, high-percentage categories. |

### Hard rules

1. **Orange is header-only.** `Colors.primary` must NOT be used for
   `buttonColor`, `backgroundColor` on interactive elements, or FAB fills.
   The only valid use is header backgrounds and the BalanceSummary card.
2. **White buttons get dark text.** When using `buttonColor="#fff"`, always
   set `textColor="#000"` or the text will be invisible on the dark theme.
3. **FAB icon color must contrast its background.** White FAB → dark icon.
   Orange FAB (if ever used) → white icon.
4. **No emoji in UI.** All icons use the custom `Icon` component with clean
   geometric Unicode glyphs (e.g. `\u29D6`, `\u26A0`, `\u2193`). Never
   use emoji characters (🕐, ⚠️, 📊, etc.) — they render inconsistently
   across devices and look unprofessional.
5. **Use `Colors.*` constants, never hardcoded hex in screens/components.**
   The only exception is explicit `#fff`/`#000` for button text contrast.
6. **Card backgrounds use `Colors.surfaceCard`.** Do not use `#fff` or
   `Colors.background` for cards.
7. **Semantic surfaces use 8% opacity.** Income/expense/warning card
   backgrounds are `Colors.incomeSurface`, `Colors.expenseSurface`, etc.
8. **Tab bar:** 5 tabs max. Active tint is white (`Colors.textPrimary`).
   Height is 52px. Label font is 9px.
9. **Headers:** Orange background, white text. Always use safe area insets
   for top padding (`insets.top + 16`).
10. **Bottom padding:** All scrollable screens must account for tab bar
    height (52px) + margin in their `contentContainerStyle` or bottom spacer.

## Repository structure (actual)

```
/Expense_Tracker
  /backend                        FastAPI app
    main.py                       App entrypoint (CORS, lifespan, routers)
    requirements.txt              Python deps (aiosqlite, fastapi, lightgbm, etc.)
    .env                          DATABASE_URL, SECRET_KEY
    expense_tracker.db            SQLite database (auto-created on first run)
    /app
      /db
        database.py               Async engine, session factory, init_db()
      /models
        __init__.py               SQLAlchemy ORM: User, Account, Transaction, Category, RecurringRule, Prediction
      /schemas
        __init__.py               Pydantic request/response schemas
      /routes
        __init__.py
        auth.py                   POST /register, POST /login, GET /me
        accounts.py               CRUD /accounts
        transactions.py           CRUD /transactions (with filtering, balance updates)
        categories.py             CRUD /categories
        forecast.py               GET /forecast/cashflow, /runway, /anomalies
        budget.py                 GET /budget/recommendations, /category-analysis
        recurring.py              CRUD /recurring + GET /recurring/upcoming
        categorize.py             POST /categorize/suggest, /categorize/corrections, /categorize/train
      /services
        categorize.py             Keyword-to-category mapping + suggest function
        seed.py                   Default category seeding on signup
      /ml
        __init__.py
        categorizer.py            LightGBM classifier with TF-IDF features
        saved_models/             Persisted models (auto-created on train)
      /utils
        __init__.py               JWT creation, password hashing, get_current_user dependency
    /migrations                   (empty — using create_all, not Alembic yet)
    /tests                        (empty)
  /frontend                       React Native (Expo) app
    App.tsx                       Entry point with PaperProvider
    app.json                      Expo config
    package.json                  Expo SDK 51 deps
    tsconfig.json
    /src
      /api
        client.ts                 Axios + SecureStore auth interceptor
        auth.ts                   register, login, getMe
        accounts.ts               CRUD
        transactions.ts           CRUD + filters
        categories.ts             getAll, create
        forecast.ts               cashflow, runway, anomalies
        budget.ts                 recommendations, category-analysis
        recurring.ts              CRUD recurring rules + upcoming
        categorize.ts             suggest, logCorrection
      /db
        localDb.ts                expo-sqlite helpers (local-first transaction storage)
      /services
        syncService.ts            Background sync: push pending→remote, pull remote→local
      /hooks
        useNetworkSync.ts         Network status detection + auto-sync on reconnect
      /utils
        uuid.ts                   UUID generation for local records
      /store
        authStore.ts              Token persistence, login/logout/register
        accountStore.ts           Accounts state
        transactionStore.ts       Transactions + filters state
        categoryStore.ts          Categories state
        recurringStore.ts         Recurring rules + upcoming state
      /navigation
        AppNavigator.tsx          Auth stack ↔ Bottom tabs
      /screens
        /auth
          LoginScreen.tsx
          RegisterScreen.tsx
        /main
          DashboardScreen.tsx     Balance summary, recent txns, runway, quick links
          TransactionsScreen.tsx  Filtered list (all/income/expense)
          AddTransactionScreen.tsx Type picker, amount, category, account, date
          AccountsScreen.tsx      List + add dialog
          ForecastScreen.tsx      Runway, cashflow, anomalies
          BudgetScreen.tsx        Recommendations + category analysis
      /components
        Icon.tsx                  Custom text-based icon (no vector-icons dependency)
        TransactionCard.tsx
        AccountCard.tsx
        BalanceSummary.tsx
        UpcomingCard.tsx          Upcoming recurring transaction card
      /theme
        colors.ts               Color palette constants (Colors.*)
  AGENTS.md
```

## Data model (actual SQLAlchemy schema)

All tables use `String` (UUID) primary keys generated via `uuid.uuid4()`.

**users**
- id (PK), email (unique, indexed), password_hash (not-null), created_at, updated_at

**accounts**
- id (PK), user_id (FK→users, indexed), name (indexed), currency (default "USD"), initial_balance (float, default 0), current_balance (float, default 0), created_at, updated_at

**transactions**
- id (PK), user_id (FK→users, indexed), account_id (FK→accounts, indexed), type (enum: income|expense, indexed), amount (float), category (indexed), description, merchant (nullable), date (indexed), is_recurring (int, default 0), created_at, updated_at

**categories**
- id (PK), user_id (FK→users, indexed), name (indexed), parent_id (FK→categories, nullable), type (enum: income|expense), color (nullable), icon (nullable), created_at

**recurring_rules**
- id (PK), user_id (FK→users, indexed), transaction_id (FK→transactions, nullable), pattern (string), frequency (int, default 1), expected_amount (float), expected_date (datetime), last_matched (nullable), created_at

**predictions**
- id (PK), user_id (FK→users, indexed), type (indexed: cashflow|runway|anomaly|budget), data (string/JSON), generated_at, valid_until

## Build phases — implement strictly in this order

### Phase 1: Foundation (CRUD, no ML) ✅ DONE

Completed:
1. Scaffolded repo structure.
2. Set up SQLite dev database (Postgres-ready via `.env` swap).
3. Implemented all 6 tables via SQLAlchemy ORM.
4. FastAPI: Full CRUD for accounts, transactions, categories — all scoped to authenticated user.
5. JWT auth: register, login, get-me endpoints with bcrypt password hashing.
6. React Native: Auth screens (login/register), dashboard, transaction list, add-transaction form, accounts screen.
7. Zustand stores for auth, accounts, transactions, categories.

Not done yet:
- Default category seeding ✅ DONE.
- Offline SQLite cache for mobile ✅ DONE (expo-sqlite, local-first writes, background sync).

Definition of done: ✅ A user can sign up, create an account, add income and
expense transactions, and see a running balance.

### Phase 2: Recurring transactions (manual) ✅ DONE

Completed:
- Add-transaction form has a "recurring" checkbox toggle.
- Frequency selector (weekly, bi-weekly, monthly, quarterly, yearly).
- Next-date input for expected recurrence date.
- Backend CRUD for `recurring_rules`: POST /, GET /, GET /upcoming, DELETE /{id}.
- Upcoming transactions auto-generated from rules with occurrence expansion.
- Dashboard shows upcoming recurring transactions with date badges.
- Recurring rule created automatically when transaction is marked recurring.

Definition of done: ✅

### Phase 3: Naive forecasting ✅ DONE

Completed:
- Backend `/forecast/cashflow`: Rolling 3-month average of income/expenses, projected forward day-by-day from current balance.
- Backend `/forecast/runway`: Days until balance hits zero (or threshold) based on net daily burn rate.
- Backend `/forecast/anomalies`: Per-category 2x-average outlier flagging.
- Frontend ForecastScreen: Displays runway, cashflow projections, anomaly list.

Definition of done: ✅ App shows forward-looking balance projection, runway
estimate, and anomaly detection based on simple averages.

### Phase 4: Rule-based categorization ✅ DONE

Completed:
- Keyword-matching function: maps merchant/description substrings to 14 categories.
- Backend POST /api/categorize/suggest returns suggested category + confidence level.
- Frontend: debounced auto-suggest chip appears after 3 chars typed in description/merchant.
- User can accept (checkmark) or dismiss (X) the suggestion.
- Corrections logged to correction_logs table when user overrides suggestion.
- POST /api/categorize/corrections stores: description, merchant, suggested, corrected.

Definition of done: ✅

### Phase 5: ML-based categorization (LightGBM) ✅ DONE

Completed:
- `backend/app/ml/categorizer.py`: LightGBM classifier with TF-IDF features.
- TfidfVectorizer (1-3 gram, 2000 features) on description + merchant text.
- LightGBM multiclass classifier (14 categories).
- Model saved/loaded from disk (`backend/app/ml/saved_models/`).
- Minimum 30 correction samples required to train.
- Confidence threshold (0.55) — falls back to rules when ML confidence is low.
- POST /api/categorize/train — trains model on all correction_logs data.
- GET /api/categorize/model-info — returns training status.
- Frontend API updated with source field ("ml" / "rules" / "none").
- Cold-start fallback: rule-based keyword matching until enough data.

Definition of done: ✅ Model trains on correction data, predicts with confidence
scores, falls back to rules when data is insufficient.

### Phase 6: Cash flow forecasting model — NAIVE VERSION DONE

Completed:
- Backend `/forecast/cashflow` uses rolling 3-month average (naive model).
- Frontend displays the projection.

Not done (ML upgrade):
- LightGBM regressors for income/expense forecasting.
- Feature engineering (seasonality, spend velocity, etc.).
- Prediction caching in `predictions` table.
- Confidence ranges in the chart.

Definition of done: ✅ NAIVE VERSION — ML upgrade pending Phase 5.

### Phase 7: Runway prediction ✅ DONE

Completed:
- Backend `/forecast/runway`: Computes days until balance hits threshold using net daily burn rate.
- Frontend DashboardScreen shows runway prominently.

Definition of done: ✅ Users see runway estimate. Will be upgraded when Phase 6 gets ML models.

### Phase 8: Anomaly detection ✅ DONE

Completed:
- Backend `/forecast/anomalies`: Per-category 2x-average outlier flagging.
- Frontend ForecastScreen displays anomalies with severity.

Definition of done: ✅ Unusually large transactions are flagged. Will be upgraded to Isolation Forest later.

### Phase 9: Budget recommendations ✅ DONE

Completed:
- Backend `/budget/recommendations`: Rule-based budget caps per category based on historical average + income percentage.
- Backend `/budget/category-analysis`: Full spending breakdown by category.
- Frontend BudgetScreen: Shows recommendations and category analysis with progress bars.

Definition of done: ✅ Users get suggested budgets per category.

### Phase 10: Auto-recurrence detection — NOT DONE

Deferred until Phases 1–9 are stable with real user data.

## What to do next (priority order)

1. **Alembic migrations** — Replace `create_all` with proper migration workflow.
2. **Prediction caching** — Write scheduled predictions to `predictions` table.
3. **Phase 6 upgrade: ML cashflow forecasting** — LightGBM regressors for income/expense.
4. **Switch to Supabase** — When ready for production: swap auth to Supabase Auth, swap DB to Supabase Postgres.

## Conventions the agent must follow throughout

- **ML models:** load once at module level, not per-request. Batch process
  rather than loop row-by-row where possible. Guard every model-serving code
  path against empty/sparse input (new users have no history — fall back to
  naive heuristics, never crash or return nonsense).
- **No required live external API calls for core ML inference** — models
  must run fully locally after training. External pip-installable
  dependencies are fine.
- **API endpoints:** namespace clearly — `/accounts`, `/transactions`,
  `/forecast/cashflow`, `/forecast/runway`, `/budget/recommend`.
  All endpoints scoped to the authenticated user; never return another
  user's data.
- **Predictions are cached, not computed live on every request** — write to
  the `predictions` table via scheduled jobs, read from cache in the API.
- **Every ML phase (5, 6, 8, 9) needs a documented fallback for users without
  enough data.** Do not ship a phase where cold-start users get an error or
  an empty state with no explanation.
- **Python:** type hints throughout; keep Pydantic models accurate rather
  than passing raw dicts through FastAPI.
- **React Native:** small components, shared logic in hooks, keep screens
  under the phase's scope — don't build ahead of the current phase's UI needs.
- **No `@expo/vector-icons`**: Causes runtime errors in Expo Go. Use the
  custom `Icon` component at `frontend/src/components/Icon.tsx` with Unicode
  glyphs. Do not add `react-native-vector-icons` or `expo-font`.
- **Product copy/comments:** be concrete about what each ML feature actually
  does; avoid vague "AI-powered" language in UI text or code comments.

## What "done" means for the whole project (v1)

Phases 1–9 complete, each with its Definition of Done satisfied, running
against a real (even if small) set of user data, deployed (backend on
Railway/Render, mobile build shareable via Expo). Phase 10 is optional for
v1 and can ship as a v1.1 update.
