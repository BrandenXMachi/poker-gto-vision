# Deployment Guide - lelabubu.ca

This guide covers deploying the Poker GTO Vision project to Render with the custom domain lelabubu.ca.

## Prerequisites

- GitHub account
- Render account (https://render.com)
- Access to Network Solutions DNS management for lelabubu.ca

---

## Step 1: Push to GitHub

1. Initialize git repository (if not already done):
```bash
cd poker-gto-vision
git init
```

2. Create a new repository on GitHub
   - Go to https://github.com/new
   - Name it: `poker-gto-vision`
   - Keep it private or public as preferred
   - Do NOT initialize with README (we already have files)

3. Add and commit files:
```bash
git add .
git commit -m "Initial commit - Poker GTO Vision"
```

4. Push to GitHub:
```bash
git remote add origin https://github.com/YOUR_USERNAME/poker-gto-vision.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy Backend to Render

1. **Log into Render Dashboard**
   - Go to https://dashboard.render.com

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `poker-gto-vision` repository

3. **Configure Backend Service**
   - **Name**: `poker-gto-vision-backend`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   - Click "Environment" tab
   - Add:
     - `PYTHON_VERSION` = `3.11`
     - `FRONTEND_URL` = `https://lelabubu.ca`

5. **Add Persistent Disk (for models)**
   - Go to "Disks" tab
   - Click "Add Disk"
   - **Name**: `models`
   - **Mount Path**: `/opt/render/project/src/backend/models`
   - **Size**: 1 GB

6. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete (5-10 minutes)
   - Note the backend URL: `https://poker-gto-vision-backend.onrender.com`

---

## Step 3: Deploy Frontend to Render

1. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Select same `poker-gto-vision` repository

2. **Configure Frontend Service**
   - **Name**: `poker-gto-vision-frontend`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Runtime**: Node
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`

3. **Add Environment Variables**
   - Click "Environment" tab
   - Add:
     - `NODE_VERSION` = `18`
     - `NEXT_PUBLIC_WS_URL` = `wss://poker-gto-vision-backend.onrender.com`
       - Note: Use `wss://` (secure WebSocket) for production
       - Replace with your actual backend URL from Step 2

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

---

## Step 4: Configure Custom Domain on Render

1. **Go to Frontend Service Settings**
   - Navigate to your frontend service dashboard
   - Click "Settings" tab

2. **Add Custom Domain**
   - Scroll to "Custom Domains" section
   - Click "Add Custom Domain"
   - Enter: `lelabubu.ca`
   - Click "Save"

3. **Add www Subdomain**
   - Click "Add Custom Domain" again
   - Enter: `www.lelabubu.ca`
   - Click "Save"

4. **Note DNS Instructions**
   - Render will show DNS records you need to configure
   - **For lelabubu.ca**: You'll get an A record or CNAME
   - **For www.lelabubu.ca**: You'll get a CNAME record
   - Keep this page open for the next step

---

## Step 5: Update DNS at Network Solutions

**IMPORTANT**: Only do this when you're ready to switch the domain!

1. **Log into Network Solutions**
   - Go to your account and find DNS management for lelabubu.ca

2. **Update A Record** (or CNAME if provided by Render)
   - **Type**: A (or CNAME)
   - **Host**: @ (or leave blank)
   - **Value**: [IP address or hostname from Render]
   - **TTL**: 3600

3. **Update WWW CNAME Record**
   - **Type**: CNAME
   - **Host**: www
   - **Value**: [CNAME from Render, typically ends in .onrender.com]
   - **TTL**: 3600

4. **Verify Existing MX Records** (Email must keep working!)
   - Ensure these MX records remain:
   ```
   Priority 10: mx1.networksolutions.com
   Priority 20: mx2.networksolutions.com
   ```

5. **Save Changes**
   - DNS propagation takes 24-48 hours
   - Use https://dnschecker.org to monitor propagation

---

## Step 6: Verify SSL Certificate

1. **Wait for DNS Propagation**
   - Can take minutes to 48 hours
   - Check https://lelabubu.ca periodically

2. **Render Auto-SSL**
   - Render automatically provisions SSL certificates
   - Once DNS propagates, SSL will be active
   - Look for padlock icon in browser

3. **Force HTTPS**
   - Render automatically redirects HTTP to HTTPS
   - Test: http://lelabubu.ca should redirect to https://lelabubu.ca

---

## Step 7: Update Backend CORS

Once the domain is live, verify CORS is working:

1. The backend is already configured for:
   - https://lelabubu.ca
   - https://www.lelabubu.ca

2. If you encounter CORS issues:
   - Check backend logs in Render dashboard
   - Verify `FRONTEND_URL` environment variable is set correctly

---

## Step 8: Test the Deployment

1. **Test Frontend Access**
   - Visit https://lelabubu.ca
   - Should load the Poker GTO Vision app

2. **Test WebSocket Connection**
   - Click "Start Analysis"
   - Check browser console for WebSocket connection
   - Status indicator should turn green

3. **Test Camera Access**
   - Allow camera permissions
   - Verify video feed displays

4. **Test Backend Communication**
   - Monitor browser console for WebSocket messages
   - Backend should be processing frames

---

## Monitoring & Logs

### View Logs in Render

1. **Backend Logs**
   - Go to backend service dashboard
   - Click "Logs" tab
   - Monitor for errors or WebSocket connections

2. **Frontend Logs**
   - Go to frontend service dashboard
   - Click "Logs" tab

### Common Issues

**WebSocket Connection Fails**
- Verify `NEXT_PUBLIC_WS_URL` uses `wss://` not `ws://`
- Check backend URL is correct
- Ensure backend service is running

**CORS Errors**
- Verify `FRONTEND_URL` environment variable on backend
- Check allowed_origins in backend/main.py

**Camera Not Working**
- HTTPS is required for camera access (SSL must be working)
- Check browser permissions
- Test on mobile device with back camera

---

## Updating the Application

### After Making Code Changes

1. **Commit and Push to GitHub**
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

2. **Render Auto-Deploys**
   - Render automatically detects changes
   - Both services will rebuild and redeploy
   - Monitor deployment progress in dashboard

### Manual Redeploy

If needed, you can manually trigger deployment:
- Go to service dashboard
- Click "Manual Deploy" → "Deploy latest commit"

---

## Rollback

If something goes wrong:

1. **Render Rollback**
   - Go to service dashboard
   - Click on "Events" or deployment history
   - Select previous successful deployment
   - Click "Rollback"

2. **DNS Rollback**
   - Change DNS records back to old server
   - Wait for propagation

---

## Environment Variables Summary

### Backend
- `PYTHON_VERSION`: 3.11
- `FRONTEND_URL`: https://lelabubu.ca

### Frontend
- `NODE_VERSION`: 18
- `NEXT_PUBLIC_WS_URL`: wss://poker-gto-vision-backend.onrender.com

---

## Security Notes

1. **Never commit .env files**
   - Already in .gitignore
   - Only use .env.example as templates

2. **Keep Dependencies Updated**
```bash
# Backend
pip install --upgrade -r backend/requirements.txt

# Frontend
cd frontend && npm update
```

3. **Monitor Logs**
   - Check for suspicious activity
   - Watch for errors

---

## Support Resources

- **Render Docs**: https://render.com/docs
- **Next.js Docs**: https://nextjs.org/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Network Solutions Support**: https://www.networksolutions.com/support

---

## Quick Reference

**Production URLs**:
- Frontend: https://lelabubu.ca
- Backend: https://poker-gto-vision-backend.onrender.com

**GitHub Repository**:
- https://github.com/YOUR_USERNAME/poker-gto-vision

**DNS Provider**:
- Network Solutions

---

Last Updated: 2025-11-29
