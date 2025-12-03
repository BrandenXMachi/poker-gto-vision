# Railway Deployment Fix Guide

## Current Status
✅ Railway connected to GitHub
✅ Two services created automatically:
- poker-gto-vision-backend (FAILED)
- poker-gto-vision-frontend (FAILED)

## What You Need To Do

### Step 1: Check Why Backend Failed
1. In Railway, click on **"poker-gto-vision-backend"** (left sidebar)
2. Click **"View logs"** button
3. Look for the error message
4. Common issues:
   - Wrong build/start commands
   - Missing environment variables
   - Root directory not set

### Step 2: Configure Backend Service

1. Click **"Settings"** tab for backend service
2. Configure these settings:

**Root Directory:**
```
backend
```

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Environment Variables:**
Add these in Variables tab:
- `PYTHON_VERSION` = `3.11.0`
- `FRONTEND_URL` = `https://your-frontend-url.railway.app` (we'll update this later)

### Step 3: Configure Frontend Service

1. Click **"Settings"** tab for frontend service
2. Configure these settings:

**Root Directory:**
```
frontend
```

**Build Command:**
```
npm install && npm run build
```

**Start Command:**
```
npm start
```

**Environment Variables:**
Add in Variables tab:
- `NODE_VERSION` = `18`
- `NEXT_PUBLIC_WS_URL` = `wss://your-backend-url.railway.app` (we'll update after backend deploys)

### Step 4: Deploy Order

1. **Backend first:**
   - Configure backend settings (above)
   - Click "Deploy" or it will auto-deploy
   - Wait for success
   - Copy the backend URL (e.g., `https://poker-gto-vision-backend-production.up.railway.app`)

2. **Then frontend:**
   - Update `NEXT_PUBLIC_WS_URL` variable with backend URL (use `wss://` not `https://`)
   - Deploy frontend
   - Wait for success
   - Copy the frontend URL

3. **Update backend:**
   - Go back to backend Variables
   - Update `FRONTEND_URL` with the frontend URL
   - Redeploy

### Step 5: Add Custom Domain (lelabubu.ca)

After both services work:
1. Go to frontend service → Settings
2. Click "Add Domain"
3. Add `lelabubu.ca`
4. Railway will show you DNS records
5. Update DNS at Network Solutions

---

## Quick Actions NOW:

1. **Click "View logs"** on the failed backend to see the actual error
2. **Go to Settings** for backend service
3. **Set Root Directory** to `backend`
4. Let it redeploy

Report back what the error logs say!
