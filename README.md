# Etimad Tenders Monitor — نظام مراقبة مناقصات اعتماد

A production-grade full-stack system that automatically monitors Saudi Etimad public tenders, matches them against company interests using AI, and sends HTML email alerts.

---

## Architecture

```
etimad/
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── api/           # REST endpoints
│   │   ├── core/          # Config, logging
│   │   ├── db/            # SQLAlchemy session
│   │   ├── models/        # ORM models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Scraper, matcher, email
│   │   └── tasks/         # APScheduler jobs
│   ├── alembic/           # Database migrations
│   └── requirements.txt
├── frontend/              # Next.js 15 dashboard
│   └── src/
│       ├── app/           # App Router pages
│       ├── components/    # UI + dashboard components
│       ├── lib/           # API client, utilities
│       └── types/         # TypeScript types
├── docker/                # Dockerfiles + postgres init
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### 1. Clone and configure environment

```bash
cp .env.example .env
# Edit .env — fill in SMTP, OpenAI key, database password
```

### 2. Docker (recommended)

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000
- Frontend dashboard: http://localhost:3000
- API docs (Swagger): http://localhost:8000/docs

### 3. Local development

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium --with-deps

# Copy and fill .env
cp ../.env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
cp ../.env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

## Database Migrations

```bash
cd backend

# Apply all migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1

# View migration history
alembic history
```

---

## REST API

| Method | Endpoint            | Description                        |
|--------|---------------------|------------------------------------|
| GET    | /api/v1/tenders     | List tenders (paginated, filtered) |
| GET    | /api/v1/tenders/:id | Get single tender                  |
| POST   | /api/v1/scrape/run  | Trigger scrape job (background)    |
| POST   | /api/v1/matching/run| Trigger AI matching + notifications|
| GET    | /api/v1/jobs/status | Check if jobs are running          |
| GET    | /health             | Health check                       |

### Query parameters for GET /api/v1/tenders

| Param              | Type    | Description                     |
|--------------------|---------|---------------------------------|
| search             | string  | Full-text search                |
| is_relevant        | bool    | Filter by AI match result       |
| notification_sent  | bool    | Filter by notification status   |
| entity             | string  | Filter by government entity     |
| activity           | string  | Filter by activity field        |
| page               | int     | Page number (default: 1)        |
| page_size          | int     | Items per page (default: 20)    |

---

## Environment Variables

| Variable                  | Required | Description                          |
|---------------------------|----------|--------------------------------------|
| DATABASE_URL              | ✅       | Async PostgreSQL URL (asyncpg)        |
| DATABASE_URL_SYNC         | ✅       | Sync PostgreSQL URL (psycopg2)        |
| SECRET_KEY                | ✅       | App secret key                        |
| SMTP_HOST                 | ✅       | SMTP server hostname                  |
| SMTP_PORT                 | ✅       | SMTP port (587 for TLS)               |
| SMTP_USER                 | ✅       | SMTP username / email                 |
| SMTP_PASSWORD             | ✅       | SMTP password / app password          |
| SMTP_FROM                 | ✅       | Sender email address                  |
| OPENAI_API_KEY            | ⬜       | OpenAI API key (falls back to keyword)|
| OPENAI_MODEL              | ⬜       | Model (default: gpt-4o-mini)          |
| SCRAPER_INTERVAL_MINUTES  | ⬜       | Scrape interval (default: 60)         |
| SCRAPER_HEADLESS          | ⬜       | Run browser headless (default: true)  |
| COMPANY_NAME              | ⬜       | Your company name (Arabic)            |
| COMPANY_ACTIVITIES        | ⬜       | Comma-separated activity keywords     |
| RELEVANCE_THRESHOLD       | ⬜       | Match score threshold (default: 0.6)  |

---

## Scheduler

APScheduler runs three jobs automatically:

| Job                | Interval                    | Description                            |
|--------------------|-----------------------------|----------------------------------------|
| `scrape_tenders`   | Every `SCRAPER_INTERVAL_MINUTES` | Scrape all Etimad pages          |
| `match_tenders`    | Every `INTERVAL / 2` min    | Run AI matching on unprocessed tenders |
| `send_notifications` | Every 15 minutes          | Send email alerts for relevant tenders |

---

## AI Matching

- **With OpenAI key**: Uses GPT-4o-mini to analyze each tender against the company profile and returns `is_relevant`, `confidence_score`, and a reason in Arabic.
- **Without OpenAI key**: Falls back to keyword matching using `COMPANY_ACTIVITIES`.

---

## Testing

```bash
# Backend: test health endpoint
curl http://localhost:8000/health

# Trigger a scrape manually
curl -X POST http://localhost:8000/api/v1/scrape/run

# Trigger matching
curl -X POST http://localhost:8000/api/v1/matching/run

# List tenders
curl "http://localhost:8000/api/v1/tenders?page=1&page_size=5"

# Filter relevant only
curl "http://localhost:8000/api/v1/tenders?is_relevant=true"

# Frontend type-check
cd frontend && npm run type-check
```

---

## Security Notes

- All secrets loaded from `.env` via `pydantic-settings` — never hardcoded
- `.env` is gitignored
- Raw HTML is capped at 200KB per tender
- Input validation via Pydantic on all API endpoints
- CORS is open for development; restrict `allow_origins` in production
- Use a real `SECRET_KEY` in production (32+ random chars)
