# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Checklist

- [ ] Node.js 18+ installed
- [ ] Python 3.10+ installed
- [ ] Phone and laptop on same WiFi
- [ ] Poker video ready to test with

## Installation (One-Time Setup)

### 1. Backend Setup

```bash
# Navigate to backend
cd poker-gto-vision/backend

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# OR for Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Install dependencies (10-15 min first time)
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# Navigate to frontend
cd poker-gto-vision/frontend

# Install dependencies (2-3 min)
npm install
```

## Running the App

### Terminal 1 - Backend

```bash
cd poker-gto-vision/backend
# Activate venv if needed
python main.py
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### Terminal 2 - Frontend

```bash
cd poker-gto-vision/frontend
npm run dev
```

Wait for: `Local: http://localhost:3000`

### Phone Access

1. Find your laptop IP:
   - Windows: `ipconfig` → IPv4 Address
   - Mac: `ifconfig | grep inet`

2. Open phone browser, go to:
   ```
   http://YOUR_LAPTOP_IP:3000
   ```

3. Grant camera permission

4. Press "Start Analysis"

5. Point at poker video on laptop screen

6. Listen for audio recommendations!

## Troubleshooting Quick Fixes

**Can't connect from phone?**
- Check both devices on same WiFi
- Try phone's IP in browser (should load)
- Disable firewall temporarily

**Camera won't start?**
- Try different browser (Chrome recommended)
- Check browser permissions
- For iOS: may need HTTPS (use ngrok)

**No audio?**
- Check phone volume
- Unmute browser tab
- Check browser allows audio

**Backend errors?**
- Check Python version: `python --version`
- Reinstall: `pip install -r requirements.txt`

**Frontend won't build?**
- Check Node version: `node --version`
- Delete node_modules, run `npm install` again

## Testing Without Phone

For quick testing on your laptop:

1. Start backend and frontend as above
2. Open `http://localhost:3000` in your browser
3. Allow camera access
4. Point laptop camera at a screen showing poker

## Where to Go Next

- Read `README.md` for full documentation
- See `SETUP.md` for detailed configuration
- Adjust detection thresholds in `backend/cv/detector.py`
- Customize audio in `frontend/app/page.tsx`

## Need Help?

Common issues and solutions in `SETUP.md` → "Troubleshooting" section
