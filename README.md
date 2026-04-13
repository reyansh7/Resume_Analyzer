# 🚀 Resume Analyzer - Production Ready

AI-powered resume analysis application with Gemini integration for skill roadmaps.

**Status**: ✅ **Production Ready for Render Deployment**

## Quick Links

- 📋 [Render Deployment Guide](RENDER_DEPLOYMENT.md) - Complete step-by-step deployment
- ✅ [Production Checklist](PRODUCTION_CHECKLIST.md) - All production fixes verified
- 🔒 [Environment Setup](backend/.env.production.example) - Secure configuration

## Key Features

✅ Resume PDF upload and parsing  
✅ ATS compatibility scoring  
✅ Skill extraction and matching  
✅ Experience highlights extraction  
✅ Job description similarity matching  
✅ AI-powered learning roadmaps (Gemini)  
✅ Dashboard with analytics  
✅ Responsive mobile-first UI  

## Tech Stack

| Component | Technology | Port |
|-----------|-----------|------|
| Frontend | Next.js 14 + TypeScript + Tailwind | 3000 |
| Backend | Express.js + MongoDB + JWT | 8080 |
| ML | FastAPI + scikit-learn + spaCy | 8000 |
| Database | MongoDB Atlas (Cloud) | - |

## Services Architecture

```
Web Browser
    ↓
Frontend (Next.js) ← Authentication & API ← Backend (Express)
    ↓                                              ↓
                                        ML Service (FastAPI)
                                        ↓
                                    MongoDB Atlas
```

## Prerequisites

- **Node.js**: 20+
- **Python**: 3.11+
- **Docker**: Optional (recommended for production-like environment)
- **MongoDB**: Free Atlas account (https://www.mongodb.com/cloud/atlas)

---

## Local Development

### Option A: Docker Compose (Recommended)

```bash
# Build and start all services
docker compose up --build

# Access services
# Frontend:     http://localhost:3000
# Backend:      http://localhost:8080
# ML Service:   http://localhost:8000
# MongoDB:      localhost:27017

# Stop all services
docker compose down
```

### Option B: Manual Setup (4 Terminals)

**Terminal 1: MongoDB**
- Use MongoDB Atlas or local MongoDB
- No setup needed if using Docker

**Terminal 2: ML Service**
```bash
cd ml-model
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 3: Backend**
```bash
cd backend
npm install
cp .env.example .env
# Edit .env: ML_SERVICE_URL=http://localhost:8000
npm run dev
```

**Terminal 4: Frontend**
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

---

## Environment Variables

### Backend (.env)

Required for production:
```env
NODE_ENV=production
PORT=8080
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/resume_analyzer
JWT_SECRET=<GENERATE_32_CHAR_RANDOM_STRING>
CORS_ORIGIN=https://your-frontend-domain.com
```

See [backend/.env.production.example](backend/.env.production.example) for all options.

### Frontend (.env.local)

Required:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080/api
```

For production:
```env
NEXT_PUBLIC_BACKEND_URL=https://your-backend-domain.com/api
```

See [frontend/.env.production.example](frontend/.env.production.example) for production setup.

---

## Production Deployment on Render

### 🚀 Quick deployment:

```bash
# 1. Generate secure JWT secret
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# 2. Push to GitHub
git add . && git commit -m "Production ready" && git push origin main

# 3. Follow RENDER_DEPLOYMENT.md for complete setup
```

### What's Included for Production

✅ All hardcoded secrets removed  
✅ Environment variables properly configured  
✅ Health check endpoints  
✅ Global error handlers  
✅ MongoDB connection pooling  
✅ Next.js optimizations (gzip, image opt, etc.)  
✅ Security headers configured  
✅ Optimized Dockerfiles with multi-stage builds  
✅ Non-root Docker users for security  
✅ CORS properly enforced  
✅ Rate limiting configured  
✅ Graceful shutdown handlers  

See [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) for detailed verification.

---

## API Documentation

### Health Checks
```bash
GET /health                    # Backend health
GET http://localhost:8000/health    # ML service health
```

### Authentication
```bash
POST /api/auth/login          # Login with email/password
POST /api/auth/register       # Create new account
POST /api/auth/logout         # Logout
```

### Resume Analysis
```bash
POST /api/resume/analyze      # Upload and analyze resume (PDF)
GET /api/resume/history       # Get all analyses
DELETE /api/resume/:id        # Delete analysis
```

### Example: Analyze Resume
```bash
curl -X POST http://localhost:8080/api/resume/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@resume.pdf"
```

---

## Troubleshooting

### Frontend can't connect to Backend
```bash
# Check NEXT_PUBLIC_BACKEND_URL in .env.local
# Ensure backend is running: curl http://localhost:8080/health
# For production: ensure CORS_ORIGIN matches frontend URL
```

### PDF upload fails
```bash
# Ensure file is valid PDF
# Check file size (max ~50MB)
# Verify ML service is running
# Check backend logs for errors
```

### MongoDB connection fails
```bash
# Verify MONGODB_URI is correct
# For Atlas: check network access includes your IP
# Test connection: mongosh "$MONGODB_URI"
```

### Performance issues
```bash
# Check MongoDB connection pool: MONGO_MAX_POOL_SIZE=10
# Verify all 3 services are running
# Check available memory
# Scale up Render plan if needed
```

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for more troubleshooting.

---

## Project Structure

```
resume-analyzer/
├── frontend/                 # Next.js app
│   ├── app/                 # Routes and pages
│   ├── components/          # Reusable components
│   ├── services/            # API client
│   ├── Dockerfile           # Production build
│   └── next.config.mjs      # Production optimizations
│
├── backend/                 # Express API
│   ├── src/
│   │   ├── controllers/     # Request handlers
│   │   ├── services/        # Business logic
│   │   ├── middleware/      # Express middleware
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Utilities
│   ├── Dockerfile           # Production build
│   └── tsconfig.json        # TypeScript config
│
├── ml-model/                # FastAPI service
│   ├── app/
│   │   ├── main.py         # FastAPI app
│   │   ├── pipelines/      # ML pipelines
│   │   ├── services/       # Business logic
│   │   └── models/         # ML models
│   ├── Dockerfile          # Production build
│   └── requirements.txt     # Python dependencies
│
├── docker-compose.yml       # Local development
├── docker-compose.prod.yml  # Production reference
├── RENDER_DEPLOYMENT.md     # Deployment guide
└── PRODUCTION_CHECKLIST.md  # Verification list
```

---

## Security

### Implemented
✅ JWT authentication  
✅ CORS policy enforcement  
✅ Rate limiting (20 req/15min per IP)  
✅ Security headers (helmet)  
✅ Input validation (Zod)  
✅ No hardcoded secrets  
✅ Non-root Docker users  
✅ HTTPS-ready  

### Best Practices
- Store secrets in environment variables
- Regenerate JWT_SECRET for each environment
- Restrict MongoDB network access
- Enable HTTPS in production
- Monitor error logs
- Regular security audits

---

## Scaling

| Component | Free | Starter | Standard |
|-----------|------|---------|----------|
| Frontend | ✅ | $7/mo | $12/mo |
| Backend | ✅ | $7/mo | $12/mo |
| ML Service | ✅ | $7/mo | $12/mo |
| MongoDB | ✅ M0 | M2 $9/mo | M5+ $57/mo |

---

## Getting Help

- **Render Documentation**: https://render.com/docs
- **MongoDB Atlas**: https://docs.mongodb.com/atlas/
- **Next.js**: https://nextjs.org/docs
- **FastAPI**: https://fastapi.tiangolo.com/

---

## License

Proprietary

---

**Last Updated**: April 13, 2026  
**Status**: ✅ Production Ready
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

## Vercel deployment checklist

### Architecture for production

- Deploy `frontend/` on **Vercel**.
- Deploy `backend/` on a long-running Node host (Render/Railway/Fly/VM).
- Deploy `ml-model/` on a long-running Python host (Render/Railway/VM).

`backend/` and `ml-model/` are persistent services and should not be deployed as Vercel serverless functions.

### 1) Frontend (Vercel)

In Vercel project settings for `frontend/`, set:

```dotenv
NEXT_PUBLIC_BACKEND_URL=https://your-backend-domain.com/api
```

Then deploy the `frontend/` root directory.

### 2) Backend (Node host)

Set these env vars for `backend/`:

```dotenv
NODE_ENV=production
PORT=8080
MONGODB_URI=your_mongodb_uri
MONGODB_DB_NAME=resume_analyzer
JWT_SECRET=your_strong_random_secret_min_32_chars
JWT_EXPIRES_IN=1d
JWT_COOKIE_NAME=access_token
CORS_ORIGIN=https://your-app.vercel.app,https://*.vercel.app
ML_SERVICE_URL=https://your-ml-service-domain.com
STORE_RAW_RESUME_TEXT=false
RESUME_TEXT_MAX_CHARS=4000
USE_IN_MEMORY_DB=false
```

Notes:
- `CORS_ORIGIN` supports comma-separated origins and wildcard subdomain patterns like `https://*.vercel.app`.
- In production, weak `JWT_SECRET` values are rejected at startup.

### 3) ML service (Python host)

Deploy `ml-model/` with:

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Recommended production env for custom model behavior:

```dotenv
USE_RESUME_CLASSIFIER=true
```

### 4) Final verification

- Open frontend URL on Vercel.
- Login/register succeeds.
- Resume upload and `/api/resume/analyze/v2` succeeds.
- Backend `/health` and ML `/health` both return `ok`.

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
