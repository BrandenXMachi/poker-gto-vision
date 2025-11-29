# Setup Guide - Poker GTO Vision

Detailed step-by-step setup instructions for getting the system running.

## System Requirements

### Hardware
- **Laptop/PC**: Modern computer with WiFi (minimum 8GB RAM recommended)
- **Smartphone**: iPhone or Android with:
  - Camera (preferably good quality)
  - Modern browser (Chrome, Safari, Firefox)
  - WiFi connectivity
  - Recommended: phone stand/holder for stable positioning

### Software
- **Node.js**: Version 18 or higher ([Download](https://nodejs.org/))
- **Python**: Version 3.10 or higher ([Download](https://www.python.org/))
- **Git**: For cloning the repository (optional)

## Installation Steps

### 1. Set Up Python Environment (Backend)

#### Windows

```cmd
# Navigate to backend directory
cd poker-gto-vision\backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Mac/Linux

```bash
# Navigate to backend directory
cd poker-gto-vision/backend

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: First installation may take 10-15 minutes as it downloads PyTorch, YOLOv8, and EasyOCR models.

### 2. Set Up Frontend

```bash
# Navigate to frontend directory
cd poker-gto-vision/frontend

# Install dependencies
npm install
```

This should take 2-3 minutes.

### 3. Configure Network Access

#### Find Your Laptop's IP Address

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your WiFi adapter (e.g., `192.168.1.100`)

**Mac:**
```bash
ifconfig | grep "inet "
```

**Linux:**
```bash
hostname -I
```

#### Update Frontend Configuration (Optional for Production)

If deploying to a server, edit `frontend/app/page.tsx`:

```typescript
// Change this line:
const ws = new WebSocket('ws://localhost:8000/ws')

// To your server IP:
const ws = new WebSocket('ws://YOUR_SERVER_IP:8000/ws')
```

## Running the Application

### Step 1: Start Backend Server

```bash
# In backend directory
cd poker-gto-vision/backend

# Activate virtual environment if not already active
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Run server
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start Frontend Development Server

In a **new terminal**:

```bash
# In frontend directory
cd poker-gto-vision/frontend

# Run development server
npm run dev
```

You should see:
```
▲ Next.js 14.x.x
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000
```

### Step 3: Access from Phone

1. **Ensure both devices are on the same WiFi network**
2. On your phone's browser, navigate to:
   ```
   http://YOUR_LAPTOP_IP:3000
   ```
   Example: `http://192.168.1.100:3000`

3. **Grant camera permissions** when prompted

## First-Time Usage

### Testing the Setup

1. **Start a test**: Press "Start Analysis" button
2. **Check connection**: Look for green "Connected" indicator
3. **Point at screen**: Aim camera at your laptop screen showing a poker video
4. **Listen**: When action buttons appear on screen, you should hear audio recommendations

### Troubleshooting Camera Issues

If camera doesn't start:
- **iOS Safari**: Camera must be accessed via HTTPS or localhost. For local network access, you may need to:
  1. Generate self-signed certificate
  2. Or use ngrok/tunneling service
  
- **Android Chrome**: Should work with HTTP on local network

- **Permission denied**: Check browser settings → Site permissions → Camera

### Troubleshooting Connection Issues

**"Failed to connect to server"**
- Verify backend is running (`http://localhost:8000` should show status page)
- Check firewall settings (allow port 8000)
- Ensure both devices are on same network
- Try using laptop IP instead of `localhost`

**"WebSocket error"**
- Backend may have crashed - check terminal for errors
- Restart backend server
- Check that no other service is using port 8000

## Performance Optimization

### Backend Performance

**For better FPS:**
- Use CUDA-enabled GPU if available (edit requirements.txt to use `torch` with CUDA)
- Reduce frame processing resolution in `detector.py`
- Use lighter YOLOv8 model (yolov8n.pt vs yolov8s.pt)

**For lower latency:**
- Increase frame capture rate in frontend (change `100ms` interval)
- Use WebRTC instead of WebSocket (advanced)
- Deploy backend closer to users

### Frontend Performance

**Battery saving:**
- Reduce frame rate (increase interval from 100ms to 200ms)
- Lower camera resolution in `getUserMedia` settings

## Advanced Configuration

### Custom YOLO Model

If you've trained a custom model:

1. Place model file in `backend/models/poker_detector.pt`
2. Backend will automatically load it on startup

### OCR Language Support

To support other languages, edit `backend/cv/ocr.py`:

```python
self.reader = easyocr.Reader(['en', 'es', 'fr'], gpu=False)
```

### Adjusting Detection Sensitivity

Edit `backend/cv/detector.py`:

```python
# Hero turn detection threshold
button_threshold = 500  # Lower = more sensitive, Higher = more conservative
```

### Changing Audio Voice

Edit `frontend/app/page.tsx`:

```typescript
const utterance = new SpeechSynthesisUtterance(text)
utterance.rate = 1.2  // Speed (0.1 to 10)
utterance.pitch = 1.0  // Pitch (0 to 2)
utterance.volume = 1.0  // Volume (0 to 1)
```

## Production Deployment

### Backend Deployment Options

1. **Cloud VM** (AWS EC2, Google Cloud, DigitalOcean)
2. **Docker Container** (create Dockerfile)
3. **Heroku** with Python buildpack

### Frontend Deployment Options

1. **Vercel** (recommended for Next.js)
2. **Netlify**
3. **Build static and host anywhere**

### HTTPS Setup

For production on mobile:
- Use Let's Encrypt for SSL certificate
- Configure reverse proxy (nginx)
- Update WebSocket URL to use `wss://` instead of `ws://`

## Maintenance

### Updating Dependencies

**Backend:**
```bash
pip install --upgrade -r requirements.txt
```

**Frontend:**
```bash
npm update
```

### Logs and Debugging

**Backend logs**: Terminal output shows all detection events
**Frontend logs**: Browser console (F12 on desktop, developer mode on mobile)

## Common Issues

### Issue: High CPU usage

**Solution**: 
- Reduce frame rate
- Use smaller YOLO model (yolov8n instead of yolov8s)
- Reduce camera resolution

### Issue: Audio recommendations cut off

**Solution**:
- Increase cooldown in `game/state.py`
- Check browser TTS settings

### Issue: Detection not working

**Solution**:
- Verify good camera angle (straight-on view)
- Improve lighting
- Reduce screen glare
- Test with different poker videos

### Issue: Slow frame processing

**Solution**:
- Check CPU/RAM usage
- Close other applications
- Use GPU acceleration (install CUDA-enabled PyTorch)

## Getting Help

1. Check logs in both terminal windows
2. Verify all prerequisites are installed correctly
3. Test with minimal setup (one poker video)
4. Review browser console for errors

## Next Steps

Once running successfully:
1. Test with various poker videos
2. Adjust detection thresholds based on your setup
3. Consider training custom YOLO model for your specific use case
4. Explore the code to understand and customize behavior
