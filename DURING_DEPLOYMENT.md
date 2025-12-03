# What's Happening Now & What's Next

## Backend Deployment In Progress

You just clicked "Deploy Web Service" for the backend. Here's what to expect:

### During Deployment (5-10 minutes):
- You'll see a logs screen with text scrolling
- Render is installing Python dependencies
- Building the FastAPI backend
- Starting the uvicorn server

### Look For:
- "Build succeeded" message
- "Deploy succeeded" message
- A URL like: `https://poker-gto-vision-backend.onrender.com`

### ⚠️ IMPORTANT: Save the Backend URL!
Once deployment succeeds, you'll see a URL at the top of the page.
**WRITE IT DOWN** - you need it for the frontend!

Example: `https://poker-gto-vision-backend-xxxx.onrender.com`

Your backend URL: _________________________________

---

## After Backend Deploys Successfully:

### Next Step: Deploy Frontend

1. Go back to main dashboard (click "Render" logo top-left)
2. Click **"New +"** → **"Web Service"**
3. Select **poker-gto-vision** repository again
4. Click **"Connect"**

### Frontend Configuration:

**Name**: `poker-gto-vision-frontend`

**Root Directory**: `frontend`

**Build Command**: `npm install && npm run build`

**Start Command**: `npm start`

**Environment Variables**:
1. `NODE_VERSION` = `18`
2. `NEXT_PUBLIC_WS_URL` = `wss://[YOUR-BACKEND-URL]`
   - Use the URL you saved above!
   - Make sure it starts with `wss://` (not `https://`)
   - Example: `wss://poker-gto-vision-backend-xxxx.onrender.com`

**Plan**: Free

Then click **"Create Web Service"**

---

## After BOTH Services Deploy:

### Switch the Domain:

1. **Remove from OLD service:**
   - Go to "lelabubu-backend" service → Settings
   - Remove www.lelabubu.ca from Custom Domains

2. **Add to NEW frontend:**
   - Go to "poker-gto-vision-frontend" service → Settings
   - Add custom domain: `lelabubu.ca`
   - Add custom domain: `www.lelabubu.ca`

3. **Update DNS if needed:**
   - If Render shows different DNS records, update in Network Solutions
   - Otherwise, domain will automatically switch

---

## Wait Now:
Let the backend finish deploying. Watch the logs. When you see "Deploy succeeded", save the URL and proceed to deploy the frontend!
