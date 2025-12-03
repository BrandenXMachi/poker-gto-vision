# What To Do Next - Quick Actions

You're in Render dashboard with your old labubu2 backend. Now let's deploy the NEW poker-gto-vision project:

## Step 1: Deploy NEW Backend (5 minutes)

1. **In Render Dashboard**, click the **"New +"** button (top right corner)
2. Select **"Web Service"**
3. Click **"Build and deploy from a Git repository"**
4. Look for **"poker-gto-vision"** repository (NOT labubu-backend)
5. Click **"Connect"** next to poker-gto-vision

### Configure the Backend:

**Name**: `poker-gto-vision-backend`

**Root Directory**: `backend` (IMPORTANT!)

**Build Command**: `pip install -r requirements.txt`

**Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment Variables** (click "Add Environment Variable"):
- `PYTHON_VERSION` = `3.11`
- `FRONTEND_URL` = `https://lelabubu.ca`

**Plan**: Free (or Starter if you prefer)

6. Click **"Create Web Service"** at bottom
7. Wait ~5-10 minutes for it to build
8. **IMPORTANT**: Once deployed, copy the backend URL (e.g., `https://poker-gto-vision-backend.onrender.com`)
   Write it here: _________________________________

---

## Step 2: Deploy NEW Frontend (5 minutes)

1. Click **"New +"** again → **"Web Service"**
2. Click **"Build and deploy from a Git repository"**
3. Select **"poker-gto-vision"** repository
4. Click **"Connect"**

### Configure the Frontend:

**Name**: `poker-gto-vision-frontend`

**Root Directory**: `frontend` (IMPORTANT!)

**Build Command**: `npm install && npm run build`

**Start Command**: `npm start`

**Environment Variables**:
- `NODE_VERSION` = `18`
- `NEXT_PUBLIC_WS_URL` = `wss://poker-gto-vision-backend.onrender.com`
  (Replace with YOUR actual backend URL from Step 1)

**Plan**: Free (or Starter)

5. Click **"Create Web Service"**
6. Wait ~5-10 minutes for deployment

---

## Step 3: Switch Domain to New Frontend (2 minutes)

### A. Remove domain from OLD backend:
1. Go to your **"lelabubu-backend"** service (the old one)
2. Click **"Settings"**
3. Find **"Custom Domains"** section
4. Remove **www.lelabubu.ca** (click X or delete button)

### B. Add domain to NEW frontend:
1. Go to your **"poker-gto-vision-frontend"** service (the new one)
2. Click **"Settings"**
3. Scroll to **"Custom Domains"**
4. Click **"Add Custom Domain"**
5. Enter: `lelabubu.ca` → Save
6. Click **"Add Custom Domain"** again
7. Enter: `www.lelabubu.ca` → Save

### C. Note DNS Records:
Render will show you DNS records for:
- lelabubu.ca: ________________
- www.lelabubu.ca: ________________

---

## Step 4: Update DNS (If Needed)

If Render shows DIFFERENT DNS records than what's currently set:
1. Log into Network Solutions
2. Update the A record (or CNAME) for lelabubu.ca
3. Update the CNAME for www.lelabubu.ca
4. Wait 24-48 hours for propagation

If DNS records are the SAME, you're done! The domain will automatically point to the new frontend.

---

## Step 5: Test (2 minutes)

1. Wait a few minutes after adding domains
2. Visit https://lelabubu.ca
3. Should see Poker GTO Vision app (not your old site)
4. Click "Start Analysis" - status should turn green
5. Test camera functionality

---

## Summary

**What you're doing:**
- OLD: labubu-backend running at www.lelabubu.ca (Flask app)
- NEW: poker-gto-vision-backend + poker-gto-vision-frontend at lelabubu.ca (FastAPI + Next.js)

**Current step:** Deploy both new services, then switch the domain from old backend to new frontend.

---

**Start with Step 1 above - Click "New +" in Render to deploy the backend!**
