# Exact Steps From Your Current Screen

## What You See Now:
- "New Web Service" page
- "Source Code" section with "Git Provider" tab
- List showing "BrandenXMachi / lelabubu-backend"

## What To Do RIGHT NOW:

### 1. Find poker-gto-vision Repository
In the search box at the top, type: `poker-gto-vision`

OR

Scroll down in the repository list to find:
**BrandenXMachi / poker-gto-vision**

### 2. Click "Connect"
Once you see "poker-gto-vision" in the list, click the **"Connect"** button next to it.
(NOT the old "lelabubu-backend" - look for "poker-gto-vision")

---

## After Clicking Connect, You'll See Configuration Page:

### Fill in these fields:

**Name**: 
Type: `poker-gto-vision-backend`

**Region**: 
Leave as default or choose closest to you

**Branch**: 
Should be `main` (already selected)

**Root Directory**: 
Type: `backend`
⚠️ This is CRITICAL - type exactly: backend

**Build Command**:
Type: `pip install -r requirements.txt`

**Start Command**:
Type: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Scroll down to Environment Variables:

Click **"Add Environment Variable"** button and add:

**First variable:**
- Key: `PYTHON_VERSION`
- Value: `3.11`

Click **"Add Environment Variable"** again:

**Second variable:**
- Key: `FRONTEND_URL`
- Value: `https://lelabubu.ca`

### Instance Type:
Choose **Free** (or Starter if you prefer better performance)

### At the bottom:
Click **"Create Web Service"**

---

## What Happens Next:
- Render will start building your backend
- Takes ~5-10 minutes
- You'll see logs scrolling
- When done, you'll see "Deploy succeeded" and a URL like: https://poker-gto-vision-backend.onrender.com

**SAVE THAT URL!** You need it for the frontend deployment.

---

**START NOW:** Use the search box to find "poker-gto-vision" and click Connect!
