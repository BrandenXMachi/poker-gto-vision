# Deployment Checklist - lelabubu.ca

Use this checklist to track your deployment progress.

## ✅ Preparation (Completed)
- [x] Backend CORS configured for lelabubu.ca domain
- [x] Frontend WebSocket URL configurable via environment variable
- [x] Environment variable examples created (.env.example files)
- [x] Deployment configuration files created (render.yaml)
- [x] Comprehensive deployment guide created (DEPLOYMENT.md)
- [x] .gitignore configured to protect sensitive files

## 📋 Next Steps (Your Action Required)

### 1. Push to GitHub
- [ ] Initialize git repository in poker-gto-vision folder
- [ ] Create new GitHub repository named `poker-gto-vision`
- [ ] Add remote and push code to GitHub
- [ ] Verify all files are pushed correctly

**Commands:**
```bash
cd poker-gto-vision
git init
git add .
git commit -m "Initial commit - Poker GTO Vision for lelabubu.ca"
git remote add origin https://github.com/YOUR_USERNAME/poker-gto-vision.git
git branch -M main
git push -u origin main
```

### 2. Deploy Backend on Render
- [ ] Log into Render Dashboard (https://dashboard.render.com)
- [ ] Create new Web Service
- [ ] Connect GitHub repository
- [ ] Configure service:
  - Name: `poker-gto-vision-backend`
  - Root Directory: `backend`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables:
  - `PYTHON_VERSION` = `3.11`
  - `FRONTEND_URL` = `https://lelabubu.ca`
- [ ] Add persistent disk for models (1GB, mount at `/opt/render/project/src/backend/models`)
- [ ] Click Create Web Service and wait for deployment
- [ ] Note the backend URL (e.g., `https://poker-gto-vision-backend.onrender.com`)

### 3. Deploy Frontend on Render
- [ ] Create new Web Service in Render
- [ ] Use same GitHub repository
- [ ] Configure service:
  - Name: `poker-gto-vision-frontend`
  - Root Directory: `frontend`
  - Build Command: `npm install && npm run build`
  - Start Command: `npm start`
- [ ] Add environment variables:
  - `NODE_VERSION` = `18`
  - `NEXT_PUBLIC_WS_URL` = `wss://[YOUR-BACKEND-URL]`
    - **Important**: Replace `[YOUR-BACKEND-URL]` with actual backend URL from step 2
    - Use `wss://` (secure WebSocket) not `ws://`
- [ ] Click Create Web Service and wait for deployment
- [ ] Test the Render URL to ensure frontend loads

### 4. Configure Custom Domain
- [ ] Go to frontend service Settings in Render
- [ ] Add custom domain: `lelabubu.ca`
- [ ] Add custom domain: `www.lelabubu.ca`
- [ ] Note the DNS records provided by Render:
  - A record or CNAME for lelabubu.ca: ________________
  - CNAME for www.lelabubu.ca: ________________

### 5. Update DNS (When Ready!)
**⚠️ WARNING**: This will switch your domain from labubu2 to poker-gto-vision

- [ ] Log into Network Solutions DNS management
- [ ] Backup current DNS settings (screenshot or write down)
- [ ] Update A record (or CNAME) for lelabubu.ca with Render values
- [ ] Update CNAME for www.lelabubu.ca with Render values
- [ ] Verify MX records remain unchanged:
  - Priority 10: mx1.networksolutions.com
  - Priority 20: mx2.networksolutions.com
- [ ] Save DNS changes
- [ ] Wait 24-48 hours for DNS propagation

### 6. Verify Deployment
- [ ] Wait for DNS to propagate (check https://dnschecker.org)
- [ ] Visit https://lelabubu.ca
- [ ] Verify SSL certificate (padlock icon in browser)
- [ ] Test WebSocket connection (Status should turn green)
- [ ] Test camera access on mobile device
- [ ] Monitor Render logs for any errors
- [ ] Test full functionality:
  - [ ] Camera captures video
  - [ ] WebSocket connects successfully
  - [ ] Backend processes frames
  - [ ] Recommendations appear when testing

## 🔍 Troubleshooting

### WebSocket Won't Connect
- Verify `NEXT_PUBLIC_WS_URL` uses `wss://` (not `ws://`)
- Check backend service is running in Render dashboard
- Review backend logs for errors

### CORS Errors
- Verify `FRONTEND_URL` environment variable on backend = `https://lelabubu.ca`
- Check backend/main.py allowed_origins configuration

### Camera Not Working
- HTTPS/SSL must be working (required for camera access)
- Test on mobile device (phones typically have better cameras)
- Check browser permissions

### DNS Not Updating
- DNS can take up to 48 hours
- Use https://dnschecker.org to monitor
- Try different device/network
- Clear browser cache

## 📞 Support

If you encounter issues:
1. Check DEPLOYMENT.md for detailed instructions
2. Review Render logs (both frontend and backend)
3. Check browser console for JavaScript errors
4. Consult Render documentation: https://render.com/docs

## 🎯 Success Criteria

Your deployment is complete when:
- ✅ https://lelabubu.ca loads the Poker GTO Vision app
- ✅ SSL certificate is active (padlock icon)
- ✅ WebSocket connects (green status indicator)
- ✅ Camera access works on mobile
- ✅ Backend processes frames and provides recommendations
- ✅ No CORS errors in browser console

---

**Estimated Time**: 
- GitHub push: 5 minutes
- Render deployment: 15-20 minutes
- DNS update: Instant (propagation: 24-48 hours)
- Total active work: ~30 minutes + waiting for DNS

**Cost**: 
- Render free tier covers both services
- Consider upgrading for better performance if needed

---

Last Updated: 2025-11-29
