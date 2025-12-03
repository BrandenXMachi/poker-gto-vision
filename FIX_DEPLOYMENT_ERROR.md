# Fix Backend Deployment Error

## The Problem:
The deployment failed with error:
"The PYTHON_VERSION must provide a major, minor, and patch version, e.g. 3.8.1. You have requested 3.11."

## The Fix:

### Step 1: Go to Environment Settings
1. In your current "poker-gto-vision-backend" page
2. Click **"Environment"** in the left sidebar
3. Find the environment variable: `PYTHON_VERSION`

### Step 2: Update Python Version
Change the value from:
- ❌ `3.11`

To:
- ✅ `3.11.0`

(Render requires the full version with patch number)

### Step 3: Redeploy
1. Click **"Manual Deploy"** button (top right)
2. Select **"Clear build cache & deploy"**
3. Wait for the new deployment (5-10 minutes)

---

## Alternative: Delete and Recreate

If the above doesn't work:

### Option A: Delete This Service and Start Fresh
1. Click **"Settings"** (left sidebar)
2. Scroll to bottom
3. Click **"Delete Web Service"**
4. Confirm deletion

Then create a NEW service with the correct settings:
- Name: `poker-gto-vision-backend`
- Root Directory: `backend`
- Environment Variable: `PYTHON_VERSION` = `3.11.0` (not 3.11)
- Environment Variable: `FRONTEND_URL` = `https://lelabubu.ca`

---

**Quick Fix Now:** Go to Environment tab → Change PYTHON_VERSION to `3.11.0` → Click "Manual Deploy"
