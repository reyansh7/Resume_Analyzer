# 🎯 QUICK START: Production Deployment on Render

## ⚡ 5-Minute Setup

### 1. Generate JWT Secret
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```
**Save this value** - you'll need it for all environments.

### 2. Verify Files Are Ready
```bash
# Should see all TRUE
docker-compose.yml ✅
RENDER_DEPLOYMENT.md ✅
backend/Dockerfile ✅
frontend/Dockerfile ✅
ml-model/Dockerfile ✅
```

### 3. Push to GitHub
```bash
git add .
git commit -m "Production ready deployment"
git push origin main
```

## 📋 Step-by-Step Deployment (30 mins total)

### Step 1: MongoDB Atlas (10 mins)

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create cluster → M0 (Free)
3. Create user → Username: `resumeuser`, Password: (generate strong)
4. Network Access → Add `0.0.0.0/0`
5. **Copy connection string**: `mongodb+srv://resumeuser:PASSWORD@cluster0...`

### Step 2: Render Backend (10 mins)

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. **New +** → **Web Service**
3. Connect GitHub repo, select `main` branch
4. Configuration:
   - Root Directory: `backend`
   - Build: `npm install && npm run build`
   - Start: `npm start`
   - Plan: Free (or Starter if needed)
5. Environment Variables (click Add):
   ```
   JWT_SECRET = [YOUR_GENERATED_SECRET]
   MONGODB_URI = [YOUR_ATLAS_CONNECTION_STRING]
   MONGODB_DB_NAME = resume_analyzer
   NODE_ENV = production
   CORS_ORIGIN = [WILL_UPDATE_LATER]
   ```
6. Click **Deploy** → Wait 3-5 mins

### Step 3: Render ML Service (10 mins)

1. **New +** → **Web Service**
2. Same repo, select `main`, Root Directory: `ml-model`
3. Configuration:
   - Environment: Python 3.11
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Plan: Starter ($7/month - Python needs it)
4. Environment Variables:
   ```
   USE_GEMINI_ROADMAP = false
   ```
5. Click **Deploy**

### Step 4: Render Frontend (5 mins)

1. **New +** → **Web Service**
2. Same repo, select `main`, Root Directory: `frontend`
3. Configuration:
   - Build: `npm install && npm run build`
   - Start: `npm start`
   - Plan: Free
4. Environment Variables:
   ```
   NEXT_PUBLIC_BACKEND_URL = https://[BACKEND_URL].onrender.com/api
   NODE_ENV = production
   ```
5. Click **Deploy**

### Step 5: Update Backend CORS (2 mins)

After frontend finishes deploying:

1. Go to Backend service → Settings → Environment
2. Update `CORS_ORIGIN`:
   ```
   CORS_ORIGIN = https://[FRONTEND_URL].onrender.com
   ```
3. **Redeploy** backend

## ✅ Test Everything

```bash
# 1. Test health endpoints
curl https://[BACKEND_URL].onrender.com/health
curl https://[ML_URL].onrender.com/health

# 2. Access frontend
https://[FRONTEND_URL].onrender.com

# 3. Test login
Click "Login" → Create test account

# 4. Test resume upload
Upload PDF → Should show analysis

# 5. Check results
- Skills extracted ✅
- Experience shown ✅
- Certifications detected ✅
```

## 🔧 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| **CORS Error** | Check `CORS_ORIGIN` matches frontend URL exactly, restart backend |
| **Can't Connect to DB** | Verify `MONGODB_URI` correct, check Atlas network access = `0.0.0.0/0` |
| **PDF Upload Fails** | Ensure file is valid PDF, under 50MB, ML service running |
| **Slow Performance** | Upgrade from Free to Starter plan |
| **ML Service Error** | Upgrade ML to Starter ($7/mo minimum) |

## 📚 Full Guides

- **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)** - Complete detailed guide (600+ lines)
- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Verification checklist
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - Summary of all changes

## 🎯 Key URLs After Deployment

```
Frontend   → https://resume-analyzer-frontend.onrender.com
Backend    → https://resume-analyzer-backend.onrender.com/api
ML Service → https://resume-analyzer-ml.onrender.com
```

## 📞 Need Help?

Common issues are in **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md#troubleshooting)**

## ⏱️ Timeline

- **Pre-deployment**: 5 mins (generate secrets, push to Git)
- **MongoDB setup**: 10 mins
- **Backend deploy**: 5 mins (+ 3-5 min wait)
- **ML deploy**: 5 mins (+ 3-5 min wait)
- **Frontend deploy**: 5 mins (+ 3-5 min wait)
- **Configuration update**: 2 mins
- **Testing**: 5 mins
- **Total**: ~45 minutes first time

---

**That's it!** Your app is now on Render. 🎉

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for full details.
