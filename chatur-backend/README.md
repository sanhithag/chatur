# CHATUR Backend

Intelligent Adaptive Learning Platform backend built with FastAPI, SQLAlchemy 2.0 (async), SQLite (aiosqlite), and Alembic.

## Prerequisites

- Python 3.10+
- virtualenv / pip

## Quick Start

1. Install dependencies:
```bash
pip install -e .
```

2. Configure environment:
```bash
cp .env.example .env
```

3. Seed database:
```bash
python -m app.seed
```

4. Start development server:
```bash
uvicorn app.main:app --reload --port 8000
```

5. Access interactive API documentation:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Multi-subject, multilingual content (added)

**New in this version**
- `learn/active?subject_id=...` keeps recommendations inside the chosen subject (prerequisite- and mastery-aware); progress stays per concept, so switching subjects never resets anything.
- `GET /curriculum/subjects/{id}/navigator?grade=` powers the Subject → Class → Chapter → Concept picker on Learn. `GET /students/{id}/subjects/progress` powers dashboard progress (real counts).
- Lessons are stored as structured JSON (`concept_lessons`, status draft → generated → validated → approved). Only **approved** lessons reach students. Translations (`lesson_translations`) are cached per lesson version and language; if the AI provider is down the English lesson is shown with a visible notice.
- Approving a lesson mirrors its practice questions into `questions`, so Solve/Test/BKT work unchanged (te/hi text included once translated).
- Admin → Curriculum shows exact coverage and a review queue with Approve.

**Setup**
```bash
cd chatur-backend
cp .env.example .env          # set AI_PROVIDER=gemini|anthropic and the matching key (optional)
alembic upgrade head          # on an old DB created by create_all: `alembic stamp 0001_initial_schema` first
python -m app.pipeline.run seed                              # verified curriculum (idempotent)
python -m app.pipeline.run generate --subject MATH --grade 10 --limit 5   # resumable; needs AI key
python -m app.pipeline.run translate --lang te,hi            # approved lessons only
python -m app.pipeline.run report                            # exact counts
```
Set `REFERENCE_DIR` to a local folder of NCERT chapter PDFs (named like `jemh104.pdf`) to ground generation. PDFs are never bundled. Without an AI key the app serves stored lessons/translations only.

**Verified curriculum currently seeded** (chapter titles read from the supplied NCERT PDFs): Class 10 Science (13 ch.), Class 10 Mathematics (14 ch.; topics from numbered section headings, may be incomplete), Class 9 Social Science Part 1 (9 ch.), Class 9 English *Kaveri* (8 units). Other classes/subjects need their NCERT sources added to `app/data/verified_curriculum.json`.
