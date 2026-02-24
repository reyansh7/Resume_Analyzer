# Resume Analyzer (Production-Ready AI SaaS Skeleton)

Modern AI-powered resume and skill-gap analysis platform built with separated microservices:

- `frontend/` → Next.js 14 + TypeScript + Tailwind + Framer Motion + GSAP + TanStack Query
- `backend/` → Express + Prisma + Zod + JWT + Multer
- `ml-model/` → FastAPI + spaCy + Sentence Transformers + scikit-learn cosine similarity

## Architecture

```text
Frontend -> Backend -> ML Service -> Backend -> PostgreSQL -> Frontend
```

- Frontend never calls ML directly.
- Backend orchestrates auth, validation, extraction, ML calls, and persistence.
- Parsed resume + structured analysis are stored in PostgreSQL via Prisma (`Json` fields).

## Implemented UX Flow

1. Landing page with animated hero reveal, parallax sections, counters, smooth transitions.
2. Login page with split-screen design, OAuth placeholders, focus/hover micro-interactions, shake-on-error.
3. Onboarding multi-step animated form with progress bar and profession/experience/skills capture.
4. Resume upload with drag-and-drop, hover glow, loading shimmer.
5. Dashboard with animated match score ring, staggered sections, timeline roadmap, and charts.

## Folder Structure

```text
Resume_Analyzer/
├── frontend/
├── backend/
├── ml-model/
├── docker-compose.yml
└── README.md
```

## Local Development (without Docker)

### 1) Backend

```bash
cd backend
cp .env.example .env
npm install
npx prisma generate
# Optional first migration
npx prisma migrate dev --name init
npm run dev
```

### 2) ML Service

```bash
cd ml-model
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2.1) Train Baseline Resume Classifier

This trains a first-pass category model using both:
- `ml-model/Resume/Resume.csv` (`Resume_str` + `Category`)
- `ml-model/data/<CATEGORY>/*.pdf`

```bash
cd ml-model
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python scripts/train_baseline.py
```

Optional faster run (subset PDFs):

```bash
python scripts/train_baseline.py --max-pdfs 600
```

Outputs:
- `ml-model/saved_models/resume_classifier.joblib`
- `ml-model/saved_models/resume_classifier_metrics.json`

### 3) Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Docker

```bash
docker compose up --build
```

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- ML Service: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## Security and Engineering Notes

- JWT auth middleware protects onboarding and analysis endpoints.
- Zod validation used in auth/onboarding payload handling.
- File uploads restricted to PDF and size-limited.
- CORS restricted via `CORS_ORIGIN` environment variable.
- Modular architecture with separated controllers/routes/services/pipelines.

## Next Recommended Enhancements

- Replace demo OAuth buttons with real Google + LinkedIn providers.
- Add password hashing and full credential auth flow.
- Add Redis caching and queue-based async analysis for heavy loads.
- Add test suites (unit + integration + e2e).
- Add CI/CD workflows and Sentry monitoring.
