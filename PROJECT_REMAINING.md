# Resume_Analyzer – What’s Remaining to Reach Production Quality

## 1) Current Status

Working now:
- Frontend (Next.js) runs and UI flows are implemented.
- ML FastAPI service runs locally (with spaCy optional fallback on Python 3.13).
- Backend APIs are implemented.

Blocked/partial:
- Docker is not available on your machine (`docker` command not found).
- MongoDB is not reliably available with valid credentials in current local environment.
- Model is currently rule-based + similarity baseline, not yet fully fine-tuned for high-accuracy production behavior.

---

## 2) Environment Keys (What you still need)

### Root `.env` (reference)
- `NEXT_PUBLIC_BACKEND_URL` – Frontend API base URL.
- `MONGODB_URI` – MongoDB connection string.
- `JWT_SECRET` – JWT signing secret.

### `frontend/.env.local`
- `NEXT_PUBLIC_BACKEND_URL=http://localhost:8080/api`

### `backend/.env`
- `PORT` – Backend port (default `8080`).
- `NODE_ENV` – `development|test|production`.
- `MONGODB_URI` – MongoDB connection URI.
- `MONGODB_DB_NAME` – database name.
- `JWT_SECRET` – strong secret for auth.
- `CORS_ORIGIN` – frontend origin (`http://localhost:3000`).
- `ML_SERVICE_URL` – ML endpoint (`http://localhost:8000` for local).
- `USE_IN_MEMORY_DB` – `true|false` (use `true` for local no-DB fallback).

### `ml-model/.env`
- `PYTHONUNBUFFERED=1`
- `MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2`

---

## 3) Data/Dataset Needed for Better Model Accuracy

You need **paired resume + target-role/job-skill labels** and skill ontologies. Suggested sources:

### Public datasets (starting point)
1. Kaggle resume datasets
   - Search: `resume dataset`, `resume NER`, `CV parsing`.
2. Job postings datasets
   - Kaggle / HuggingFace datasets with job title + requirements.
3. Skill taxonomies
   - O*NET (US occupation and skills data).
   - ESCO (European multilingual skills/occupations taxonomy).
   - OpenSkills API / public skill lists.
4. NER corpora (for skill/entity extraction)
   - Use to bootstrap spaCy NER fine-tuning.

Important:
- Verify each dataset’s license and terms.
- Remove PII and comply with privacy regulations before training.

---

## 4) Recommended Training Plan

## Phase A – Data pipeline
1. Build canonical schema:
   - `resume_text`, `target_role`, `gold_skills`, `seniority`, `industry`, `match_label`.
2. Normalize skills using ontology mapping (O*NET/ESCO synonyms).
3. Split data: train/val/test (stratified by role).

## Phase B – Skill extraction model
1. Baseline: dictionary + pattern matcher (already partly done).
2. Upgrade: spaCy NER fine-tuning for skill entities.
3. Evaluate with precision/recall/F1 for skill extraction.

## Phase C – Match scoring model
1. Build resume-role pairs.
2. Fine-tune sentence-transformer with contrastive/triplet loss.
3. Train regression/classification head for match % calibration.
4. Calibrate score using Platt scaling / isotonic regression.

## Phase D – Roadmap recommendations
1. Map missing skills -> curated learning graph.
2. Rank roadmap items by impact and role seniority.
3. Add rule + model hybrid ranking.

## Phase E – Evaluation & QA
1. Metrics:
   - Skill extraction F1.
   - Match score MAE / Spearman correlation with expert labels.
   - Top-k roadmap relevance.
2. Human-in-the-loop review with domain experts.
3. Add regression test suite with golden resumes.

Note:
- “Perfect output” is not realistic in NLP; target measurable quality thresholds and continuous retraining.

---

## 5) What to Implement Next (Engineering)

1. Real auth (Google + LinkedIn OAuth + secure session strategy).
2. Password hashing (if email/password stays).
3. Persistent storage in real MongoDB (disable in-memory mode in prod).
4. Async analysis jobs + queue (Redis + worker).
5. File/object storage for raw resumes (S3/Cloudinary) instead of memory-only handling.
6. Observability: Sentry + structured logs + request tracing.
7. CI/CD with automated tests.
8. Rate limiting + abuse protection + API schema docs.

---

## 6) Minimal Commands to Run Locally (No Docker)

1. ML service:
```bash
cd ml-model
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
c:/Users/reyan/OneDrive/Desktop/Resume_Analyzer/ml-model/.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. Backend (in-memory mode):
```bash
cd backend
# set USE_IN_MEMORY_DB=true in backend/.env
npm run dev
```

3. Frontend:
```bash
cd frontend
npm run dev
```

Open:
- Frontend: http://localhost:3000
- Backend health: http://localhost:8080/health
- ML health: http://localhost:8000/health

---

## 7) Production Checklist Before Launch

- [ ] Docker available and compose stack validated.
- [ ] Managed MongoDB provisioned and connectivity validated.
- [ ] Production secrets configured in deployment platform.
- [ ] OAuth credentials configured.
- [ ] Model versioning + rollback strategy.
- [ ] Data governance/privacy review complete.
- [ ] Load test + security test complete.
- [ ] Monitoring/alerting dashboards active.
