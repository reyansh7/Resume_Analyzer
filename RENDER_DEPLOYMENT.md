# 🚀 Resume Analyzer - Render Deployment Guide

## Quick Start (TL;DR)

1. **Deploy MongoDB**: Use MongoDB Atlas (free tier available)
2. **Deploy Backend**: Connect Render + GitHub repo
3. **Deploy Frontend**: Connect Render + GitHub repo
4. **Set Environment Variables**: See sections below
5. **Test**: Run health checks and integration tests

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│             Render Platform                     │
├──────────────────┬──────────────────────────────┤
│  Frontend        │  Backend      │  ML Service  │
│  (Next.js)       │  (Express)    │  (FastAPI)   │
│  Port 3000       │  Port 8080    │  Port 8000   │
└──────────────────┼──────────────────────────────┘
         │                 │               │
         └─────────────────┴───────────────┘
                    │
         ┌──────────────────────┐
         │   MongoDB Atlas      │
         │   (Database)         │
         └──────────────────────┘
```

---

## Prerequisites

- GitHub account (repository must be public or Render must have access)
- Render account (free tier works for testing)
- MongoDB Atlas account (free tier: M0 cluster)
- Domain name (optional, use Render's subdomain for testing)

---

## Step 1: Set Up MongoDB Atlas

### 1.1 Create MongoDB Atlas Cluster

1. Go to [mongo db.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create free account or login
3. Create new project: "Resume Analyzer"
4. Build a database → Select **M0 (Free)**
5. Choose deployment region (closest to your users)
6. Create cluster (takes 2-3 minutes)

### 1.2 Create Database User

1. In Atlas, go to **Database Access**
2. Add Database User:
   - Username: `resumeuser` (or any name)
   - Password: Generate strong password (copy this!)
   - Built-in roles: `Read and write to any database`
3. Add Connection IP:
   - Go to **Network Access**
   - Add IP Address: `0.0.0.0/0` (allow all - for production, restrict this)

### 1.3 Get Connection String

1. Click "Connect" button
2. Choose "Drivers" 
3. Copy connection string, looks like:
```
mongodb+srv://resumeuser:PASSWORD@cluster0.mongodb.net/resume_analyzer?retryWrites=true&w=majority
```
4. Replace `PASSWORD` with actual password

Save this for Step 3.

---

## Step 2: Prepare GitHub Repository

### 2.1 Push Code to GitHub

```bash
cd /path/to/Resume_Analyzer
git remote add origin https://github.com/YOUR_USERNAME/resume-analyzer.git
git branch -M main
git push -u origin main
```

### 2.2 Verify Repository Structure

Ensure your repo has this structure:

```
resume-analyzer/
├── backend/                 # Express API
│   ├── Dockerfile
│   ├── package.json
│   ├── .env.production.example
│   └── src/
├── frontend/                # Next.js app
│   ├── Dockerfile
│   ├── package.json
│   ├── .env.production.example
│   └── app/
├── ml-model/                # FastAPI service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── docker-compose.yml       # Local development
├── docker-compose.prod.yml  # Production (reference)
└── README.md
```

---

## Step 3: Deploy Backend Service on Render

### 3.1 Create Backend Service

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. Click **New +** → **Web Service**
3. Connect GitHub repository
4. Service configuration:
   - **Name**: `resume-analyzer-backend`
   - **Environment**: `Node`
   - **Region**: Same as MongoDB Atlas
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Plan**: `Free` (for testing) or `Starter` ($7/month)

### 3.2 Set Environment Variables (Backend)

In Render dashboard, go to Service → Settings → Environment

Add these variables:

```
NODE_ENV=production
PORT=8080
MONGODB_URI=mongodb+srv://resumeuser:PASSWORD@cluster0.mongodb.net/resume_analyzer?retryWrites=true&w=majority
MONGODB_DB_NAME=resume_analyzer
JWT_SECRET=[Generate: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"]
JWT_EXPIRES_IN=7d
CORS_ORIGIN=https://your-frontend-url.onrender.com
ML_SERVICE_URL=http://localhost:8000
STORE_RAW_RESUME_TEXT=false
RESUME_TEXT_MAX_CHARS=4000
```

⚠️ **For JWT_SECRET generation**:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 3.3 Deploy

1. Click **Deploy** button
2. Wait for deployment (usually 3-5 minutes)
3. Get service URL: `https://resume-analyzer-backend.onrender.com`

### 3.4 Verify Backend

```bash
curl https://resume-analyzer-backend.onrender.com/health
```

Should return health check response.

---

## Step 4: Deploy ML Service on Render

### 4.1 Create ML Service

⚠️ **Note**: Render free tier may have Python limitations. Use a smaller model or upgrade plan.

1. Click **New +** → **Web Service**
2. Connect same GitHub repository
3. Service configuration:
   - **Name**: `resume-analyzer-ml`
   - **Environment**: `Python 3.11`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `ml-model`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - **Plan**: `Starter` ($7/month minimum - Python needs more resources)

### 4.2 Set Environment Variables (ML)

```
USE_GEMINI_ROADMAP=false
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
```

### 4.3 Deploy & Verify

```bash
curl https://resume-analyzer-ml.onrender.com/health
```

---

## Step 5: Deploy Frontend on Render

### 5.1 Create Frontend Service

1. Click **New +** → **Web Service**
2. Connect GitHub repository
3. Service configuration:
   - **Name**: `resume-analyzer-frontend`
   - **Environment**: `Node`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Plan**: `Free` or `Starter`

### 5.2 Set Environment Variables (Frontend)

In Render dashboard:

```
NEXT_PUBLIC_BACKEND_URL=https://resume-analyzer-backend.onrender.com/api
NODE_ENV=production
```

### 5.3 Deploy & Verify

1. Click **Deploy** button
2. Wait for build/deployment
3. Once live, access: `https://resume-analyzer-frontend.onrender.com`

---

## Step 6: Update Backend CORS

After frontend is deployed, update backend CORS:

1. In Render backend dashboard → **Settings** → **Environment**
2. Update `CORS_ORIGIN`:
```
CORS_ORIGIN=https://resume-analyzer-frontend.onrender.com
```
3. Redeploy backend

---

## Step 7: Test Everything

### 7.1 Test Health Endpoints

```bash
# Backend health
curl https://resume-analyzer-backend.onrender.com/health

# ML health
curl https://resume-analyzer-ml.onrender.com/health

# Frontend
curl https://resume-analyzer-frontend.onrender.com
```

### 7.2 Test API Endpoints

```bash
# Login endpoint
curl -X POST https://resume-analyzer-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Upload resume (after authentication)
curl -X POST https://resume-analyzer-backend.onrender.com/api/resume/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@sample_resume.pdf"
```

### 7.3 Test UI

1. Go to frontend URL
2. Login with test credentials
3. Upload resume
4. Verify analysis shows up

---

## Troubleshooting

### Issue: Backend fails to start

**Symptom**: `Error: Cannot find module 'express'`

**Solution**:
```bash
# Render build command should be:
npm install --production && npm run build
```

### Issue: CORS errors

**Symptom**: Browser console shows `Access to XMLHttpRequest blocked by CORS`

**Solution**:
1. Check `CORS_ORIGIN` env var matches frontend URL exactly
2. Restart backend service
3. Check browser console for exact URL that's being blocked

### Issue: MongoDB connection fails

**Symptom**: `MongoServerError: connect ECONNREFUSED`

**Solution**:
1. Verify `MONGODB_URI` is correct (copy from Atlas again)
2. Check MongoDB Atlas network access includes `0.0.0.0/0`
3. Verify password is URL-encoded (special chars use % encoding)

### Issue: Slow uploads/timeouts

**Symptom**: PDF upload hangs after 30 seconds

**Solution**:
1. Upgrade Render plan (free tier has 30s timeout)
2. Reduce `RESUME_TEXT_MAX_CHARS` in backend env
3. Use smaller test PDFs for testing

### Issue: ML service not responding

**Symptom**: Backend returns `ML service connection failed`

**Solution**:
1. Check ML service is deployed and running
2. Verify `ML_SERVICE_URL` points to correct Render service
3. Check ML service logs for errors
4. Consider upgrading ML service to "Starter" plan

---

## Production Best Practices

### 1. **Database Backups**

Never rely on free MongoDB Atlas cluster alone. Set up:
- Monthly backups to S3
- Test restore procedures
- Document recovery RTO/RPO

### 2. **Monitoring & Logging**

Enable:
- Render logs (built-in)
- MongoDB Atlas monitoring
- Error tracking (Sentry, LogRocket)
- Application performance monitoring

### 3. **Security**

- [ ] Use strong JWT_SECRET (32+ characters)
- [ ] Enable HTTPS everywhere (Render provides free SSL)
- [ ] Restrict MongoDB IP access to Render IPs only
- [ ] Use environment variables for all secrets
- [ ] Enable API rate limiting
- [ ] Regular security audits

### 4. **Scaling**

When you outgrow free tier:

| Component | Upgrade Path |
|-----------|--------------|
| Frontend | Starter: $7/month |
| Backend | Starter: $7/month |
| ML Model | Standard: $12/month |
| Database | M2: $9/month (MongoDB Atlas) |

### 5. **Custom Domain**

1. In Render:
   - Settings → Custom Domain
   - Add your domain
   - Follow DNS configuration
2. Update environment variables:
   ```
   CORS_ORIGIN=https://yourdomain.com
   NEXT_PUBLIC_BACKEND_URL=https://api.yourdomain.com/api
   ```

---

## Environment Variables Summary

### Backend (.env)
```
# Server
NODE_ENV=production
PORT=8080

# Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/resume_analyzer?retryWrites=true&w=majority
MONGODB_DB_NAME=resume_analyzer

# Auth
JWT_SECRET=[GENERATED_SECRET]
JWT_EXPIRES_IN=7d

# CORS
CORS_ORIGIN=https://frontend-url.onrender.com

# Services
ML_SERVICE_URL=https://ml-url.onrender.com

# Options
STORE_RAW_RESUME_TEXT=false
RESUME_TEXT_MAX_CHARS=4000
MONGO_MAX_POOL_SIZE=10
MONGO_MIN_POOL_SIZE=2

# Optional: Gemini
USE_GEMINI_ROADMAP=false
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
```

### Frontend (.env.production.local)
```
NEXT_PUBLIC_BACKEND_URL=https://backend-url.onrender.com/api
NODE_ENV=production
```

### ML Model (.env)
```
USE_GEMINI_ROADMAP=false
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
```

---

## Getting Help

1. **Render Docs**: https://render.com/docs
2. **MongoDB Atlas Docs**: https://docs.mongodb.com/atlas/
3. **Next.js Deployment**: https://nextjs.org/docs/deployment
4. **Express Deployment**: https://expressjs.com/en/advanced/best-practice-performance.html

---

## Deployment Checklist

- [ ] MongoDB Atlas cluster created and configured
- [ ] GitHub repository public or Render has access
- [ ] Backend deployed on Render with env vars
- [ ] ML service deployed on Render (if needed)
- [ ] Frontend deployed on Render with env vars
- [ ] CORS_ORIGIN updated to match frontend URL
- [ ] Health check endpoints responding
- [ ] Login endpoint tested
- [ ] Resume upload tested
- [ ] Analysis results displayed correctly
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] Monitoring enabled
- [ ] Backup strategy documented

---

## Quick Redeploy

To redeploy after code changes:

```bash
# 1. Make code changes locally
git add .
git commit -m "Fix auth issues"
git push origin main

# 2. Render auto-deploys OR manually trigger:
# - Go to Render dashboard
# - Service → Settings → Manual Deploy → Deploy latest commit
```

---

**You're now production-ready! 🎉**
