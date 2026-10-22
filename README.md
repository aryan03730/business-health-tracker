# Business Health Tracker

A mobile-first web app that tells a small business owner, in about two minutes, whether the business is making money, how far it is from break-even, and what to do next.

**Live app:** _add link after deploying_ · **API:** _add link after deploying_

> The API runs on a free hosting tier and goes to sleep after 15 minutes without traffic. The first request after that can take about a minute.

| Home | Input errors | Losing money | Close call | Healthy |
|---|---|---|---|---|
| ![Home](docs/screenshots/1-home.png) | ![Validation](docs/screenshots/2-errors.png) | ![Red](docs/screenshots/5-dash-red.png) | ![Yellow](docs/screenshots/6-dash-yellow.png) | ![Green](docs/screenshots/7-dash-green.png) |

<sub>Screenshots use the worked example from the scope document. It is a test case, not real business data.</sub>

## The problem

Many small business owners (café owners, online sellers, service providers) can't easily answer a basic question: *is my business making money?* Sales and expenses are tracked in different places or not at all, accounting software is built for accountants, and a spreadsheet only helps if you already know the formulas. Owners often find out they're losing money only after the cash is gone.

This app asks for five numbers over three short screens and returns:

- a **status light** (green, yellow or red)
- **one number**: how many more sales a month are needed to break even
- **monthly profit or loss** and the **payback period**
- **one plain-English suggestion**

## How it works

```
React (Vite)  ──JSON──▶  Flask API  ──SQLAlchemy──▶  PostgreSQL
 3-step form              validation                  scenarios table
 dashboard                calculations                (inputs only)
                          suggestion rules
```

- All calculations run **on the server** in pure Python functions (`backend/calculations.py`), which keeps them easy to test.
- Only the **inputs** are stored. Results are recalculated on every request, so they always match the current formulas.
- Each saved scenario gets a random 12-character id. The dashboard lives at `/s/<id>`, so the owner can bookmark it or share it without an account.

## The calculations

Everything is per month, in a single currency (US dollars).

| Measure | Formula | Notes |
|---|---|---|
| Profit per unit | selling price − cost per unit | Must be > 0, or break-even is impossible (rejected as an input error) |
| Break-even units | monthly running costs ÷ profit per unit | |
| Break-even sales | break-even units × selling price | The same point, in dollars |
| Monthly profit or loss | (units sold × profit per unit) − monthly running costs | Negative = loss |
| Sales gap | break-even units − units sold, **rounded up** | You can't sell part of a unit. Zero or negative means costs are covered |
| Payback period | initial investment ÷ monthly profit | Only when monthly profit > 0, otherwise "Not reached" |

### Worked example (test case)

These inputs come from the project scope and are checked exactly in `backend/tests/test_calculations.py`:

| Input | Value | | Result | Value |
|---|---|---|---|---|
| Initial investment | 100,000 | | Profit per unit | 100 |
| Monthly running costs | 30,000 | | Break-even units | 300 |
| Selling price | 150 | | Break-even sales | 45,000 |
| Cost per unit | 50 | | Monthly profit or loss | −5,000 |
| Units sold | 250 | | Sales gap | 50 more units |
| | | | Status | Red |
| | | | Payback | Not reached |

## Decisions and trade-offs

**Status thresholds.** Red means the business is losing money. Yellow means it covers its costs, but units sold are less than 10% above break-even. Green means units sold are at least 10% above break-even. A 10% cushion is small enough for a normal business to reach and large enough that one slow week doesn't wipe out the profit. The margin is one constant (`GREEN_MARGIN` in `calculations.py`).

| Units sold (worked example) | 250 | 299 | 300 | 329 | 330 |
|---|---|---|---|---|---|
| Status | red | red | yellow | yellow | green |

**Saving: database plus a shareable link, no login.** Sessions-only would have been simpler, but owners come back month after month, and a link they can bookmark is the lightest way to support that. The trade-off is that anyone with the link can view and edit those numbers. The UI says this, and ids are random rather than sequential so they can't be guessed by counting.

**Rule-based suggestions.** These live in `backend/suggestions.py`. Rules run in order. The first match is shown, and any others appear under "More ideas":

1. **Losing money, gap ≤ 20% of break-even:** suggest a short, targeted promotion.
2. **Losing money, gap > 20% of break-even:** look at the largest monthly cost and test a small price increase.
3. **Cost per unit > 50% of price:** review supplier terms or get another quote.
4. **Yellow:** aim for the green threshold (a specific unit target).
5. **Payback > 24 months:** growing monthly sales is the quickest way to shorten it.
6. **Green:** keep tracking and build a cash reserve.

**Validation in two places.** The form checks inputs instantly for a smooth experience. The server checks everything again and is the source of truth. Errors come back as `{field: message}` and are shown next to the right field, and the form jumps to the step that holds the error.

**Numbers.** Money is stored as `NUMERIC(16,2)` and units as integers. Values above one trillion are rejected.

## API

Base URL: `http://localhost:5000` locally. Every response is JSON, including errors.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| POST | `/scenarios` | Save inputs. Returns `201` with id, inputs and results |
| GET | `/scenarios/{id}` | Inputs and calculated results |
| PUT | `/scenarios/{id}` | Replace the inputs. Returns the updated scenario |
| GET | `/scenarios/{id}/dashboard` | Status, sales gap, payback and suggestion |

**Request body** (POST and PUT):

```json
{
  "name": "My business",
  "initial_investment": 100000,
  "monthly_running_costs": 30000,
  "selling_price": 150,
  "cost_per_unit": 50,
  "units_sold": 250
}
```

`name` is optional (defaults to "My business", max 120 characters). Numbers may also be numeric strings.

**`GET /scenarios/{id}`**

```json
{
  "id": "aa0a3cfbe3f3",
  "name": "My business",
  "inputs": { "initial_investment": 100000.0, "monthly_running_costs": 30000.0, "selling_price": 150.0, "cost_per_unit": 50.0, "units_sold": 250 },
  "results": {
    "profit_per_unit": 100.0, "break_even_units": 300.0, "break_even_sales": 45000.0,
    "monthly_profit": -5000.0, "sales_gap_units": 50, "payback_months": null, "status": "red"
  },
  "created_at": "2026-10-22T20:01:12.000000+00:00",
  "updated_at": "2026-10-22T20:01:12.000000+00:00"
}
```

**`GET /scenarios/{id}/dashboard`**

```json
{
  "id": "aa0a3cfbe3f3",
  "name": "My business",
  "status": "red",
  "monthly_profit": -5000.0,
  "break_even_units": 300.0,
  "break_even_sales": 45000.0,
  "units_sold": 250,
  "sales_gap_units": 50,
  "payback_months": null,
  "suggestion": "You are 50 units short of break-even each month. A short, targeted promotion to your regular customers could close that gap.",
  "other_suggestions": []
}
```

**Errors**

| Status | Body |
|---|---|
| 400 | `{"error": "validation_error", "message": "Some inputs need fixing.", "fields": {"selling_price": "Selling price must be higher than the cost per unit, ..."}}` |
| 404 | `{"error": "not_found", "message": "Scenario not found."}` |
| 405 / 500 | `{"error": "...", "message": "..."}` (never an HTML stack trace) |

Validation rules: all five numbers are required. Investment, running costs, cost per unit and units sold must be ≥ 0. Selling price must be > 0 and higher than the cost per unit. Units sold must be a whole number.

## Run it locally

You need **Python 3.12+**, **Node 20+** and **PostgreSQL 14+**.

### 1. Database

```bash
psql -U postgres -c "CREATE USER bht WITH PASSWORD 'bht';"
psql -U postgres -c "CREATE DATABASE bht OWNER bht;"
```

The API creates its table on first start. If you use different credentials, set `DATABASE_URL` (see `backend/.env.example`).

### 2. API

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                                       # http://localhost:5000
```

To use another database: `export DATABASE_URL=postgresql://user:pass@host:5432/dbname` before starting.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                                         # http://localhost:5173
```

The frontend calls `http://localhost:5000` by default. To change that, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL`.

### Tests

```bash
cd backend
pytest -q                     # uses in-memory SQLite, no setup needed
# run the same tests against PostgreSQL:
createdb -U postgres -O bht bht_test
TEST_DATABASE_URL=postgresql+psycopg://bht:bht@localhost:5432/bht_test pytest -q
```

There are 47 tests: calculations (including the worked example and the status boundaries), validation messages, and every API endpoint including its error cases. GitHub Actions runs them against PostgreSQL 16 on every push, and also lints and builds the frontend.

## Deploy (free tiers)

| Piece | Host | Note |
|---|---|---|
| Database | [Neon](https://neon.tech) free plan | Render's free Postgres is deleted after 30 days, so it isn't used here |
| API | Render free web service | Sleeps after 15 min idle, takes about 1 min to wake |
| Frontend | Render static site | Free |

1. Create a Neon project and copy its connection string (`postgresql://...?sslmode=require`).
2. Push this repo to GitHub. In Render, choose **New → Blueprint** and select the repo. `render.yaml` defines both services.
3. When Render asks for environment variables, fill them in:
   - `bht-api` → `DATABASE_URL` = the Neon string, and `CORS_ORIGINS` = the frontend URL (for example `https://bht-web.onrender.com`)
   - `bht-web` → `VITE_API_URL` = the API URL (for example `https://bht-api.onrender.com`)
4. Once both are live, open `<api>/health`, then try the app on a phone. Put both links at the top of this README.

Free-tier limits change, so check each host's current pricing page before deploying.

## Project structure

```
backend/
  calculations.py     pure formulas, validation, status thresholds
  suggestions.py      plain-language suggestion rules
  models.py           Scenario table (SQLAlchemy)
  app.py              Flask app factory, routes, JSON error handling
  wsgi.py             production entry point (gunicorn)
  tests/              pytest: calculations + API
frontend/
  src/pages/          Home, Wizard (3-step form, also used to edit), Dashboard
  src/validation.js   client-side copy of the server rules
  src/api.js          fetch wrapper with friendly error messages
render.yaml           Render Blueprint
```

## Not built yet

- **AI-written suggestions (OpenAI).** Planned as an optional extension. The rule-based suggestion would stay as the fallback, so the app still works without an API key or when the AI call fails.
- **Accounts and login.** Out of scope. Links stand in for accounts.
- **History over time and charts.** Each scenario is a single month. Tracking months side by side would be the most useful next feature.
- **Multiple products.** Owners with several products enter a typical one. A weighted average across products would be more accurate.
- **Currencies other than USD.** Numbers are stored plain, so this only affects formatting.
- **Rate limiting.** The open `POST /scenarios` endpoint would need one before any real traffic.
