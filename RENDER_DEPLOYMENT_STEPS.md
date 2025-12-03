# Render Deployment Steps - Quick Guide

## ✅ Completed
- [x] Code pushed to GitHub: https://github.com/BrandenXMachi/poker-gto-vision

## 🚀 Deploy to Render (Follow These Steps)

### Step 1: Sign in to Render

1. Go to https://dashboard.render.com
2. Sign in (you can use GitHub for easy authentication)

---

### Step 2: Deploy Backend Service

#### A. Create New Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**

#### B. Connect Repository

1. Click **"Connect a repository"** or **"Build and deploy from a Git repository"**
2. If GitHub not connected, click **"Connect GitHub"**
3. Search for **"poker-gto-vision"**
4. Click **"Connect"** next to your repository

#### C. Configure Backend Service

Fill in these settings:

**Basic Info:**
- **Name**: `poker-gto-vision-backend`
- **Region**: Choose closest to you (e.g., Oregon USA)
- **Branch**: `main`
- **Root Directory**: `backend`

**Build & Deploy:**
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Choose **Free** (unless you need more resources)

#### D. Environment Variables

Scroll down to **Environment Variables**, click **"Add Environment Variable"** and add:

1. `PYTHON_VERSION` = `3.11`
2. `FRONTEND_URL` = `https://lelabubu.ca`

#### E. Advanced Options (Optional but Recommended)

1. Scroll to **"Disk"** section
2. Click **"Add Disk"**
   - **Name**: `models`
   - **Mount Path**: `/opt/render/project/src/backend/models`
   - **Size**: `1` GB

#### F. Create Service

1. Click **"Create Web Service"** (bottom of page)
2. Wait 5-10 minutes for deployment
3. **IMPORTANT**: Note the backend URL (e.g., `https://poker-gto-vision-backend.onrender.com`)
4. Write it down: _______________________________________

---

### Step 3: Deploy Frontend Service

#### A. Create New Web Service

1. Go back to dashboard
2. Click **"New +"** → **"Web Service"**

#### B. Connect Repository

1. Select **"Build and deploy from a Git repository"**
2. Choose **"poker-gto-vision"** repository
3. Click **"Connect"**

#### C. Configure Frontend Service

**Basic Info:**
- **Name**: `poker-gto-vision-frontend`
- **Region**: Same as backend
- **Branch**: `main`
- **Root Directory**: `frontend`

**Build & Deploy:**
- **Runtime**: `Node`
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm start`

**Plan:**
- Choose **Free**

#### D. Environment Variables

Click **"Add Environment Variable"** and add:

1. `NODE_VERSION` = `18`
2. `NEXT_PUBLIC_WS_URL` = `wss://[YOUR-BACKEND-URL]`
   - **IMPORTANT**: Replace `[YOUR-BACKEND-URL]` with the backend URL from Step 2D
   - Example: `wss://poker-gto-vision-backend.onrender.com`
   - Make sure to use `wss://` (secure WebSocket)

#### E. Create Service

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for deployment
3. Once deployed, test the Render URL (e.g., `https://poker-gto-vision-frontend.onrender.com`)

---

### Step 4: Add Custom Domain (lelabubu.ca)

#### A. Go to Frontend Service Settings

1. In Render dashboard, click on your **frontend service** (poker-gto-vision-frontend)
2. Click **"Settings"** tab (left sidebar)

#### B. Add Custom Domains

1. Scroll down to **"Custom Domains"** section
2. Click **"Add Custom Domain"**
3. Enter: `lelabubu.ca`
4. Click **"Save"**

5. Click **"Add Custom Domain"** again
6. Enter: `www.lelabubu.ca`
7. Click **"Save"**

#### C. Note DNS Records

After adding domains, Render will show you DNS records:
- For **lelabubu.ca**: You'll get an A record or CNAME
  - Write it down: _______________________________________
- For **www.lelabubu.ca**: You'll get a CNAME record
  - Write it down: _______________________________________

**Screenshot or write these down - you'll need them for DNS!**

---

### Step 5: Update DNS at Network Solutions

⚠️ **WARNING**: This will switch lelabubu.ca from your old site to this new one!

#### A. Log into Network Solutions

1. Go to Network Solutions account
2. Find DNS management for **lelabubu.ca**

#### B. Update DNS Records

1. **Update A Record** (or CNAME if that's what Render provided):
   - **Type**: A (or CNAME)
   - **Host**: @ (or leave blank for apex)
   - **Value**: [IP or hostname from Render - Step 4C]
   - **TTL**: 3600

2. **Update WWW CNAME**:
   - **Type**: CNAME
   - **Host**: www
   - **Value**: [CNAME from Render - Step 4C]
   - **TTL**: 3600

3. **Verify MX Records** (email must keep working!):
   - Ensure these exist:
     - Priority 10: mx1.networksolutions.com
     - Priority 20: mx2.networksolutions.com

4. **Save Changes**

#### C. Wait for DNS Propagation

- DNS takes 24-48 hours to propagate
- Check status: https://dnschecker.org/#A/lelabubu.ca
- Once propagated, SSL will automatically activate

---

### Step 6: Verify Everything Works

#### A. Test Frontend

1. Wait for DNS propagation
2. Visit https://lelabubu.ca
3. Should load Poker GTO Vision app
4. Check for SSL padlock icon

#### B. Test WebSocket Connection

1. Click **"Start Analysis"** button
2. Allow camera permissions
3. Check browser console (F12) for WebSocket connection
4. Status indicator should turn green (connected)

#### C. Test Full Functionality

1. Point camera at poker table
2. Verify video feed appears
3. Check that backend is processing frames
4. Test that analysis works

---

## 🎯 Success Checklist

- [ ] Backend deployed on Render
- [ ] Frontend deployed on Render
- [ ] Custom domains added in Render (lelabubu.ca + www)
- [ ] DNS records updated at Network Solutions
- [ ] DNS propagated (check dnschecker.org)
- [ ] https://lelabubu.ca loads correctly
- [ ] SSL certificate active (padlock icon)
- [ ] WebSocket connects (green status)
- [ ] Camera works
- [ ] Backend processes frames

---

## Troubleshooting

### Backend Build Fails
- Check Render logs
- Verify requirements.txt is correct
- Ensure Python version is 3.11

### Frontend Build Fails
- Check Node version is 18
- Verify all npm dependencies install
- Check Render logs for errors

### WebSocket Won't Connect
- Verify `NEXT_PUBLIC_WS_URL` uses `wss://` not `ws://`
- Check backend is running (not sleeping)
- Verify backend URL is correct

### Domain Not Working
- DNS can take 24-48 hours
- Check https://dnschecker.org
- Verify A/CNAME records are correct
- Clear browser cache

---

## Need Help?

If you get stuck:
1. Check Render logs for errors
2. Review DEPLOYMENT.md for detailed info
3. Check browser console (F12) for errors
4. Verify all environment variables are set correctly

---

**Estimated Time**: 30-40 minutes + 24-48 hours for DNS propagation
