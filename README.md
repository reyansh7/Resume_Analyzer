# Resume Analyzer

AI-powered resume analysis app with three services:

- `frontend/`: Next.js app (port `3000`)
- `backend/`: Express + Prisma API (port `8080`)
- `ml-model/`: FastAPI ML service (port `8000`)

---

## Prerequisites

Install these first:

- Node.js `20+` and npm
- Python `3.11+`
- Docker Desktop (only if using Docker run)
- PostgreSQL `16+` (only if running locally without Docker DB)

---

## Option A: Run everything with Docker (recommended)

From the project root:

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080`
- Backend health: `http://localhost:8080/health`
- ML service health: `http://localhost:8000/health`
- PostgreSQL: `localhost:5432`

To stop:

```bash
docker compose down
```

---

## Option B: Run locally (without Docker)

Use **three terminals** (frontend, backend, ml-model).

### 1) Start PostgreSQL

Make sure PostgreSQL is running and a database named `resume_analyzer` exists.

### 2) Run ML service
```bash
cd ml-model
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Optional env file:

```bash
copy .env.example .env
```

To enable Gemini for roadmap/advice generation in `ml-model/.env`:

```dotenv
USE_GEMINI_ROADMAP=true
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TIMEOUT_MS=8000
```

Notes:
- Gemini is used only for roadmap generation.
- Skill gaps and scoring remain deterministic in local ML logic.
- If Gemini fails/times out, the service automatically falls back to local roadmap generation.

### 3) Run backend

```bash
cd backend
copy .env.example .env
npm install
npx prisma generate
npx prisma migrate dev --name init
npm run dev
```

After copying `backend/.env.example` to `backend/.env`, update this value for local run:

```dotenv
ML_SERVICE_URL=http://localhost:8000
```

### 4) Run frontend

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Quick health checks

- Backend health: `GET http://localhost:8080/health`
- Backend API index: `GET http://localhost:8080/api`
- ML service health: `GET http://localhost:8000/health`

---

## Train baseline classifier (optional)

From `ml-model/`:

```bash
python scripts/train_baseline.py
```

Recommended robust training (improves resilience to shuffled resume sections):

```bash
python scripts/train_baseline.py --section-shuffle-copies 2 --section-shuffle-prob 0.7
```

Faster subset run:

```bash
python scripts/train_baseline.py --max-pdfs 600
```

Section-order regression check:

```bash
python scripts/validate_section_regression.py
```

Generated files:

- `ml-model/saved_models/resume_classifier.joblib`
- `ml-model/saved_models/resume_classifier_metrics.json`

---

## Common issues

- **Backend can’t reach ML service**: set `ML_SERVICE_URL=http://localhost:8000` in `backend/.env` for local runs.
- **Prisma connection errors**: verify `DATABASE_URL` and `DIRECT_URL` in `backend/.env`.
- **Frontend API errors**: verify `NEXT_PUBLIC_BACKEND_URL=http://localhost:8080/api` in `frontend/.env.local`.
