# Fynd AI Intern – Take Home Assessment 2.0

This repository contains both tasks from the assessment: Task 1 (prompt-based Yelp rating prediction) and Task 2 (two-dashboard production-style feedback system).

## Repository Structure

```
Key/
├── Task_1/
│   ├── Task_Eval.ipynb            # Main evaluation notebook (4 prompt variants)
│   ├── Notebook.ipynb             # Supporting scratch notebook
│   ├── yelp_rating_predictor.py   # Batch script for prompt-only inference
│   ├── yelp_rating_predictions.csv
│   ├── yelp_prediction_summary.csv
│   └── output.png                 # Comparison plot
│
├── Backend/
│   ├── main.py                    # FastAPI app factory
│   ├── api.py                     # Endpoints (user + admin analytics)
│   ├── database.py                # SQLAlchemy engine/session
│   ├── models.py                  # Review model
│   ├── schemas.py                 # Pydantic schemas
│   ├── Prediction.py              # LLM chain for user response/summary/action
│   ├── analytics.py               # Sentiment and priority chains
│   └── requirements.txt
│
├── user_dashboard/                # Public user-facing form
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── admin_dashboard/               # Internal admin dashboard
│   ├── index.html
│   ├── admin.js
│   └── style.css
│
└── README.md
```

## Deployments

- User dashboard: deployed to Vercel — [URL: <add-url>](https://userdashboard-ten.vercel.app/)
- Admin dashboard: deployed to Vercel — [URL: <add-url>](https://admindashboard-lime-six.vercel.app/)
- Backend API: deployed to Render — https://review-predictor-using-llm.onrender.com

Notes:
- Dashboards are hosted on Vercel (static sites). Backend is hosted on Render.

Behavior checks to verify after deployment:
- User submit flow returns AI response and persists row (verify via Admin feed).
- Admin ratings chart renders average and counts; sentiment/recommendations modals load.
- Cold-start handling shows "Waking backend" state but eventually succeeds.

## Quickstart

### Backend (FastAPI + PostgreSQL)

Prereqs: Python 3.10+, PostgreSQL (Supabase URL supported).

1) Install deps
```
cd Backend
pip install -r requirements.txt
```

2) Set env vars in `.env`
```
user=postgres
password=<your_password>
host=<your_host>
port=<your_port>
dbname=<your_db>
OPENROUTER_API_KEY=<openrouter_key>
```

3) Run locally
```
python main.py
```
Docs at http://localhost:4000/docs (uses uvicorn when run as __main__).

Key endpoints:
- POST /api/reviews — store rating+review, returns AI user response.
- GET /api/admin/reviews — full feed for admin dashboard.
- GET /api/analytics/ratings — ratings distribution for Chart.js.
- GET /api/analytics/sentiment — LLM summary of last 20 reviews.
- GET /api/analytics/recommendations — LLM-prioritized action list.

Data model: table "Review 1" with id (UUID), rating, review_text, ai_summary, ai_recommended_action, ai_response, created_at.
Operational safeguards: 2000-char guard on reviews, DB pool tuned for Render/Supabase, LLM exceptions fall back to safe canned responses, health endpoint at /health.

Security notes: CORS is open for demo; tighten to dashboard origins for production. No client-side LLM keys; all calls are server-side.

### Frontend dashboards

Static HTML/JS/CSS (no build step). To run locally, serve each folder:
```
cd user_dashboard && python -m http.server 3000
cd admin_dashboard && python -m http.server 3001
```
Set API origin in `user_dashboard/app.js` and `admin_dashboard/admin.js` (defaults point to the Render backend).

UI details:
- User: star picker, textarea, loading states, backend health pill, cold-start retry hint, shows AI response only (no internal summary leakage).
- Admin: recent review feed with stars, AI summary/action, Chart.js ratings distribution with gradients, sentiment and priority modals, manual refresh button with timestamp.

### Task 1 evaluation

- Open `Task_1/Task_Eval.ipynb` for the full prompt engineering write-up (four prompt variants, metrics table, and takeaways).
- `Task_1/yelp_rating_predictor.py` reproduces the conservative Prompt 4 run on a 150-sample subset; outputs `yelp_rating_predictions.csv` and `yelp_prediction_summary.csv`.

| Prompt | Strategy | Exact | Within ±1 | MAE | Bias | JSON OK |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Structured + rating hints | 66.0% | 97.3% | 0.37 | +0.14 | 100% |
| 2 | Few-shot anchors | **66.7%** | **98.7%** | **0.35** | **+0.09** | 100% |
| 3 | Heuristic reasoning steps | 64.7% | 98.7% | 0.37 | +0.14 | 100% |
| 4 | Conservative rule-gated | 63.3% | 98.7% | 0.38 | +0.23 | 100% |

Recommendations from evaluation:
- Default to Prompt 2 for balance of accuracy and cost.
- Use Prompt 4 as a safe fallback for vague or short inputs.

## System Design Notes

- Server-only LLM calls (OpenRouter xiaomi/mimo-v2-flash) via LangChain; no client-side keys.
- Persistence in PostgreSQL (Supabase-compatible). `Review` rows store user text, rating, AI summary, AI recommended action, and AI user response.
- Resilience: length guard on reviews, exception fallback LLM outputs, connection pooling tuned for Render/Supabase.
- Admin analytics endpoints call LLMs over recent reviews/recommendations to produce sentiment and priority summaries consumed by Chart.js UI.

Data flow:
1) User submits rating/review → POST /api/reviews → LLM creates ai_summary, ai_recommended_action, ai_user_response → row persisted → AI response returned to user.
2) Admin dashboard polls GET /api/admin/reviews and GET /api/analytics/* to render feed, chart, sentiment modal, and priority modal.

Observability/manual checks: use /health for uptime; monitor Render cold starts; verify JSON validity rates stay 100% by relying on LangChain JsonOutputParser.

## Deliverables Checklist

- GitHub repo with Task 1 notebook and Task 2 app code.
- Deployed user dashboard URL (public, no setup).
- Deployed admin dashboard URL (public, auto-refreshable data).
- Backend API URL (public) with docs.
- Short report PDF (see LaTeX source in report.tex).

Optional extensions if time permits:
- Add auth (token or basic) to admin endpoints; tighten CORS.
- Add retries/backoff around LLM calls; add structured logging for latency/JSON validity.
- Add pagination to /api/admin/reviews and chart smoothing (rolling averages) if volume grows.
