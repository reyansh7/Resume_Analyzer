# Resume Analyzer

AI-powered resume analysis app with three services:

- `frontend/`: Next.js app (port `3000`)
- `backend/`: Express + MongoDB API (port `8080`)
- `ml-model/`: FastAPI ML service (port `8000`)

---

## Prerequisites

Install these first:

- Node.js `20+` and npm
- Python `3.11+`
- Docker Desktop (only if using Docker run)
- MongoDB `7+` (only if running locally without Docker DB)

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
- MongoDB: `localhost:27017`

To stop:

```bash
docker compose down
```

---

## Option B: Run locally (without Docker)

Use **four terminals** (mongodb, frontend, backend, ml-model).

### 1) Start MongoDB

Make sure MongoDB is running on `mongodb://localhost:27017`.

### 2) Run ML service
```bash
cd ml-model
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

c:/Users/reyan/OneDrive/Desktop/Resume_Analyzer/ml-model/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
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

To enable local Ollama roadmap generation in `ml-model/.env`:

```dotenv
USE_OLLAMA_ROADMAP=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_TIMEOUT_MS=20000
OLLAMA_MAX_RETRIES=1
```

Then pull and run your Ollama model:

```bash
ollama pull deepseek-r1:8b
ollama run deepseek-r1:8b
```

Compare roadmap quality and latency between Ollama models:

```bash
cd ml-model
python scripts/benchmark_ollama_roadmap.py --models deepseek-r1:8b llama3.1:8b --runs 3 --timeout-seconds 60 --max-steps 5
```

Notes:
- Roadmap generation provider priority is: `Ollama -> Gemini -> local deterministic fallback`.
- Skill gaps and scoring remain deterministic in local ML logic.
- If Ollama or Gemini fails/times out, the service automatically falls back to local roadmap generation.

### 3) Run backend

```bash
cd backend
copy .env.example .env
npm install
npm run dev
```

After copying `backend/.env.example` to `backend/.env`, update this value for local run:

```dotenv
ML_SERVICE_URL=http://localhost:8000
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=resume_analyzer
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
- **MongoDB connection errors**: verify `MONGODB_URI` and `MONGODB_DB_NAME` in `backend/.env`.
- **Frontend API errors**: verify `NEXT_PUBLIC_BACKEND_URL=http://localhost:8080/api` in `frontend/.env.local`.

---

## Deployment security hardening

### 1) Strong JWT secret

Generate a strong secret (Windows PowerShell):

```powershell
[Convert]::ToBase64String((1..64 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 } | ForEach-Object { [byte]$_ }))
```

Set this value as `JWT_SECRET` in your backend deployment environment.
Production startup now rejects weak defaults automatically.

### 2) Restrict MongoDB IP access (Atlas)

In Atlas:

1. Go to **Network Access**.
2. Remove `0.0.0.0/0` if present.
3. Add only your backend provider egress/static IP(s).
4. Keep temporary admin IP entries time-limited.

### 3) Enforce TLS-only MongoDB connections

- Prefer `mongodb+srv://...` Atlas URI (TLS enabled by default), or
- Add `?tls=true` to `mongodb://...` URI.

Production startup now validates this and fails fast for non-local insecure URIs.

### 4) Keep services always-on

For both backend and ML deployments, use always-on / no-sleep plans to avoid cold starts.
If using Render, disable auto-suspend for these two services.

### 5) Smoke test after deployment

Verify:

- `GET /health` on backend and ML
- Login flow (`/api/auth/login`)
- Resume upload + analyze v2 (`/api/resume/analyze/v2`)
- Fallback path (v2 unavailable -> v1)
- Auth-expired redirect flow
