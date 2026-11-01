# CHATUR — Intelligent Adaptive Learning Platform

CHATUR is a full-stack adaptive learning platform for school students (Classes 6–10, CBSE). It tracks each student's mastery of concepts using **Bayesian Knowledge Tracing (BKT)**, adapts lessons and practice to what they actually know, and gives teachers, parents and admins dashboards to act on that data.

It supports multiple languages and has offline-friendly features (PWA service worker and a queue for submissions made without internet).

## Features

| Role | What they can do |
|------|------------------|
| **Student** | Dashboard (XP, streaks), adaptive lessons, concept chains, practice solving, timed tests |
| **Teacher** | Class dashboard, mastery heatmap, remedial groups, content review queue, impact view |
| **Parent** | View children's progress |
| **Admin / Super admin** | Manage schools, users and the curriculum |

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), SQLite (aiosqlite), Alembic, JWT auth (python-jose, passlib/bcrypt)
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand, Axios
- **Learning model:** BKT in `chatur-backend/app/services/bkt.py`

## Project Structure

```
chatur-main/
├── chatur-backend/          # FastAPI app
│   ├── app/
│   │   ├── api/v1/          # auth, students, teachers, parents, admin, curriculum routes
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # auth, BKT, curriculum logic
│   │   ├── seed.py          # demo data
│   │   └── main.py
│   ├── alembic/             # DB migrations
│   └── tests/
├── chatur-frontend/         # React + Vite app
│   ├── public/              # manifest.json, sw.js (PWA)
│   └── src/
│       ├── lib/             # api.ts (axios client), offlineQueue.ts
│       ├── pages/           # student, teacher, parent, admin pages
│       ├── layouts/  store/  i18n/  components/
└── pragati.html             # standalone single-file prototype
```

## Getting Started

You need **Python 3.10+** and **Node.js 18+**. Run the backend and frontend in two separate terminals.

### 1. Backend

```bash
cd chatur-backend
python -m venv venv

# Windows:        venv\Scripts\activate
# macOS / Linux:  source venv/bin/activate

pip install -e .
python -m app.seed                          # creates the DB with demo users
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/api/docs
- All routes are under `/api/v1`.

### 2. Frontend

```bash
cd chatur-frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to `http://localhost:8000`, so the backend must be running.

## Demo Accounts

Created by `python -m app.seed`:

| Role | Username | Password |
|------|----------|----------|
| Super admin | `superadmin` | `Admin@CHATUR2024` |
| Admin | `admin` | `Admin@School2024` |
| Teacher | `teacher1` | `Teacher@2024` |
| Parent | `parent1` | `Parent@2024` |
| Students | `student1` … `student5` | `Student@2024` |

> These are demo credentials only.

## Configuration

Backend settings live in `chatur-backend/app/config.py` and can be overridden with environment variables or a `.env` file inside `chatur-backend/`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | local SQLite file | Database connection |
| `SECRET_KEY` | dev key | **Change in production** — signs JWTs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `CORS_ORIGINS` | localhost:5173, :3000 | Allowed frontend origins |

Frontend: set `VITE_API_URL` (e.g. in `chatur-frontend/.env`) to point at a deployed backend. Default is `/api/v1`.

## Testing

```bash
cd chatur-backend
pip install -e ".[dev]"
pytest tests
```

## Production Build

```bash
cd chatur-frontend
npm run build      # output in dist/
```

