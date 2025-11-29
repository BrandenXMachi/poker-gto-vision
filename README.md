# Poker GTO Vision

Real-time poker GTO analysis using phone camera. Point your phone at poker videos playing on your laptop, and get instant audio recommendations when it's the hero's turn to act.

## 🎯 Features

- **Live Camera Analysis**: Uses phone camera to watch poker games in real-time
- **Hero Turn Detection**: Automatically detects when it's the hero's turn using computer vision
- **Audio Recommendations**: Provides spoken GTO advice (Fold/Call/Raise) via Text-to-Speech
- **Mobile-Optimized**: Runs directly in phone browser, no app installation needed
- **Computer Vision**: YOLOv8 object detection + OCR for poker UI elements
- **GTO Solver**: Simplified solver for action recommendations

## 🏗️ Architecture

```
┌─────────────────┐
│  Phone Camera   │
│   (React App)   │
└────────┬────────┘
         │ WebSocket
         │ (JPEG frames @ 10 FPS)
         ▼
┌─────────────────────────┐
│   Python Backend        │
│   ┌─────────────────┐   │
│   │ YOLOv8 Detector │   │
│   └────────┬────────┘   │
│            │             │
│   ┌────────▼────────┐   │
│   │  OCR Processor  │   │
│   └────────┬────────┘   │
│            │             │
│   ┌────────▼────────┐   │
│   │  Game State     │   │
│   └────────┬────────┘   │
│            │             │
│   ┌────────▼────────┐   │
│   │  GTO Solver     │   │
│   └────────┬────────┘   │
└────────────┼────────────┘
             │
             ▼
    Audio Recommendation
    (via TTS on phone)
```

## 📋 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Modern smartphone** with camera and browser
- **Laptop** to run backend server

## 🚀 Quick Start

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start Backend Server

```bash
cd backend
python main.py
```

The backend will start on `http://localhost:8000`

### 4. Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

### 5. Access from Phone

1. Connect your phone to the same WiFi network as your laptop
2. Find your laptop's local IP address:
   - **Windows**: `ipconfig` → Look for IPv4 Address
   - **Mac/Linux**: `ifconfig` → Look for inet address
3. Open phone browser and navigate to: `http://YOUR_LAPTOP_IP:3000`
4. Grant camera permissions when prompted

### 6. Usage

1. Point phone camera at poker video on your laptop screen
2. Press "Start Analysis"
3. When hero's turn is detected, you'll hear audio recommendations
4. Keep camera pointed at screen for continuous analysis

## 🔧 Configuration

### Backend Configuration

Edit `backend/main.py` to adjust:
- WebSocket host/port
- Frame processing parameters
- Detection thresholds

### Frontend Configuration

Edit `frontend/app/page.tsx` to adjust:
- Frame capture rate (default: 10 FPS)
- WebSocket URL (for deployment)
- TTS settings (voice, rate, pitch)

## 📁 Project Structure

```
poker-gto-vision/
├── frontend/              # Next.js React application
│   ├── app/
│   │   ├── page.tsx      # Main camera interface
│   │   ├── layout.tsx    # App layout
│   │   └── globals.css   # Global styles
│   └── package.json
│
├── backend/               # Python FastAPI server
│   ├── main.py           # FastAPI app & WebSocket
│   ├── cv/               # Computer vision module
│   │   ├── detector.py   # YOLOv8 detection
│   │   └── ocr.py        # OCR processing
│   ├── game/             # Game state management
│   │   └── state.py      # State tracking
│   ├── solver/           # GTO solver
│   │   └── gto.py        # Strategy calculator
│   └── requirements.txt
│
└── README.md
```

## 🎓 How It Works

### Detection Pipeline

1. **Frame Capture**: Phone captures video frames at 10 FPS
2. **Preprocessing**: Frames are enhanced (contrast, denoising, perspective correction)
3. **Hero Turn Detection**: 
   - Color detection for action buttons (green/red/yellow)
   - Timer circle detection
   - Seat highlight detection
4. **OCR Extraction**:
   - Pot size
   - Stack sizes
   - VPIP/PFR stats
5. **GTO Calculation**: Simplified solver generates recommendation
6. **Audio Output**: Text-to-Speech speaks the recommendation

### Hero Turn Detection

The system detects hero's turn using multiple signals:
- ✅ Action buttons visible (FOLD, CALL, RAISE)
- ✅ Timer circle active
- ✅ Seat glow/highlight present

Requires at least 2 signals to trigger recommendation.

## 🔮 Future Enhancements

### Phase 2 Features
- [ ] Full card detection (hero cards + board cards)
- [ ] Complete stack tracking for all players
- [ ] Action sequence tracking
- [ ] Multi-street analysis
- [ ] Position-aware recommendations

### Phase 3 Features
- [ ] Train custom YOLOv8 model on poker UI screenshots
- [ ] Implement proper range-based GTO solver
- [ ] Add hand history logging
- [ ] Support multiple poker platforms
- [ ] Advanced statistics tracking

### Phase 4 Features
- [ ] Real-time equity calculations
- [ ] ICM calculator for tournaments
- [ ] HUD overlay (optional screen display)
- [ ] Multi-table support
- [ ] Export to poker tracking software

## 🚨 Limitations (MVP)

- **Simplified GTO**: Current solver uses basic logic, not full GTO ranges
- **Generic Detection**: Not trained on specific poker platform UIs
- **Hero Turn Only**: Only provides recommendations when hero must act
- **No Card Reading**: Doesn't currently read card values
- **Single Table**: Only analyzes one table at a time

## 🤝 Training Custom Model

To improve detection accuracy, train a custom YOLOv8 model:

1. Collect poker UI screenshots (various platforms, themes)
2. Annotate images:
   - Cards (with rank/suit labels)
   - Buttons (FOLD, CALL, RAISE, CHECK)
   - Timer circles
   - Seat positions
   - Pot areas
3. Train YOLOv8:
   ```bash
   yolo train data=poker_dataset.yaml model=yolov8n.pt epochs=100
   ```
4. Place trained model in `backend/models/poker_detector.pt`

## 📝 License

MIT License - Feel free to use and modify

## ⚠️ Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with the terms of service of any poker platform you may be watching.

## 🙏 Acknowledgments

- YOLOv8 by Ultralytics
- EasyOCR
- FastAPI
- Next.js
- React

## 📞 Support

For issues, questions, or contributions, please open an issue on the repository.
