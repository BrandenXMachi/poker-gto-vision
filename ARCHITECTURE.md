# System Architecture

Detailed technical architecture and design decisions.

## Overview

Poker GTO Vision is a real-time computer vision system that analyzes poker games through a phone camera and provides GTO (Game Theory Optimal) recommendations via audio feedback.

## System Components

### 1. Frontend (Mobile Web Application)

**Technology Stack:**
- Next.js 14 (React 18)
- TypeScript
- TailwindCSS
- Native Web APIs (MediaDevices, WebSocket, SpeechSynthesis)

**Key Features:**
- Camera access via `getUserMedia()`
- Real-time frame capture (canvas-based)
- WebSocket client for bidirectional communication
- Text-to-Speech for audio output
- Mobile-responsive UI

**Data Flow:**
```
Phone Camera → Video Element → Canvas → JPEG Blob → WebSocket → Backend
Backend → WebSocket → JSON Response → TTS → Audio Output
```

### 2. Backend (Python Server)

**Technology Stack:**
- FastAPI (async web framework)
- Uvicorn (ASGI server)
- OpenCV (computer vision)
- YOLOv8 (object detection)
- EasyOCR (text recognition)
- NumPy (array operations)
- Pillow (image processing)

**Architecture Pattern:**
- Microservices-inspired modular design
- Async/await for non-blocking I/O
- WebSocket for real-time communication

## Module Breakdown

### Frontend Modules

#### `app/page.tsx` - Main Application
- Camera management
- WebSocket connection handling
- Frame capture and transmission
- Audio recommendation playback
- UI state management

**Key Functions:**
- `startCamera()`: Initialize camera stream
- `connectWebSocket()`: Establish server connection
- `startFrameCapture()`: Begin frame transmission
- `speak()`: TTS audio output
- `stopAnalysis()`: Cleanup and shutdown

### Backend Modules

#### `main.py` - API Server
- FastAPI application setup
- WebSocket endpoint
- CORS configuration
- Health check endpoint
- Frame processing orchestration

#### `cv/detector.py` - Computer Vision
- Frame preprocessing (contrast enhancement, denoising)
- Hero turn detection (color-based)
- Button detection
- Timer circle detection
- YOLO object detection integration

**Detection Methods:**
1. **Color Detection**: HSV color space analysis for buttons
2. **Circle Detection**: Hough transform for timer
3. **Object Detection**: YOLOv8 for cards, seats (future)

#### `cv/ocr.py` - Text Recognition
- EasyOCR integration
- Pot size extraction
- Stack size parsing
- VPIP/PFR statistics recognition
- Currency format parsing

#### `game/state.py` - State Management
- Game state tracking
- Hero turn cooldown logic
- Player state management
- Street tracking (preflop/flop/turn/river)
- Action sequence logging

#### `solver/gto.py` - Strategy Engine
- Simplified GTO calculations
- Action recommendation (Fold/Call/Raise)
- Bet sizing calculations
- EV estimation
- Range estimation (VPIP/PFR based)

## Data Models

### Game State
```python
@dataclass
class GameState:
    street: str                    # Current street
    pot_size: float               # Current pot
    board_cards: List[str]        # Community cards
    hero_cards: List[str]         # Hero's hole cards
    players: Dict[str, PlayerState]  # All players
    action_sequence: List[str]    # Action history
    hero_turn_active: bool        # Is it hero's turn?
```

### Detection Results
```python
{
    "hero_turn": bool,
    "buttons_visible": bool,
    "timer_active": bool,
    "cards": List[str],
    "pot_size": str,
    "stacks": Dict,
    "vpip_stats": Dict
}
```

### Recommendation
```python
{
    "action": str,              # "Fold", "Call", or "Raise to $X"
    "pot_size": str,            # "$45"
    "ev": str,                  # "+0.8bb"
    "reasoning": str            # Brief explanation
}
```

## Communication Protocol

### WebSocket Messages

**Client → Server:**
- Binary: JPEG image blob (frame data)

**Server → Client:**
- JSON: Status updates
- JSON: Recommendations

**Message Format:**
```json
{
  "type": "recommendation",
  "recommendation": {
    "action": "Call",
    "pot_size": "$45",
    "ev": "+0.8bb",
    "reasoning": "Good pot odds"
  }
}
```

## Processing Pipeline

### Frame Processing Flow

```
1. Frame Reception (WebSocket)
   ↓
2. Image Decoding (Pillow)
   ↓
3. Preprocessing (OpenCV)
   - Resize
   - CLAHE contrast enhancement
   - Denoising
   ↓
4. Detection Phase
   - Hero turn detection (color analysis)
   - OCR text extraction
   - YOLO object detection (optional)
   ↓
5. State Update
   - Update game state
   - Check hero turn status
   ↓
6. Decision Making
   - If hero's turn: compute GTO recommendation
   - Generate action + sizing + reasoning
   ↓
7. Response Transmission
   - Send JSON recommendation via WebSocket
   ↓
8. Audio Output (Client)
   - Text-to-Speech speaks recommendation
```

### Performance Characteristics

**Latency Breakdown:**
- Frame transmission: 50-100ms
- Image decoding: 10-20ms
- CV processing: 100-300ms
- OCR (if triggered): 200-500ms
- State update: <5ms
- GTO calculation: 10-50ms
- Response transmission: 10-20ms

**Total latency: ~400-1000ms** (acceptable for human decision-making)

**Throughput:**
- Target: 10 FPS
- Actual: 5-10 FPS depending on hardware
- Frames processed asynchronously (non-blocking)

## Scalability Considerations

### Current Limitations (MVP)
- Single-threaded frame processing
- CPU-only inference
- No frame buffering
- No load balancing

### Potential Optimizations

**Backend:**
1. **GPU Acceleration**: Use CUDA for YOLOv8 and OpenCV
2. **Model Optimization**: Convert to ONNX/TensorRT
3. **Parallel Processing**: Process multiple frames concurrently
4. **Frame Skipping**: Skip frames when detection succeeds
5. **Redis Cache**: Cache game state across requests

**Frontend:**
1. **Adaptive Frame Rate**: Reduce FPS when battery low
2. **WebRTC**: Lower latency than WebSocket
3. **Service Worker**: Offline capability
4. **Image Compression**: Reduce bandwidth

**Infrastructure:**
1. **Load Balancer**: Distribute across multiple backend servers
2. **CDN**: Serve frontend from edge locations
3. **WebSocket Gateway**: Handle connection pooling
4. **Monitoring**: Track latency and errors

## Security Considerations

### Current Implementation
- No authentication (local network only)
- No encryption (HTTP/WS)
- No rate limiting
- No input validation

### Production Requirements
1. **HTTPS/WSS**: Encrypted connections
2. **Authentication**: JWT or session tokens
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Sanitize all inputs
5. **CORS**: Restrict origins
6. **API Keys**: Backend authentication

## Error Handling

### Frontend
- Camera access failure → Show error message
- WebSocket disconnect → Automatic reconnection attempt
- Frame capture error → Silent skip, continue
- TTS failure → Log error, continue

### Backend
- Frame decode error → Log, send status to client
- Detection failure → Return empty detections
- OCR crash → Fallback to no OCR data
- YOLO error → Continue without object detection

## Testing Strategy

### Unit Tests
- CV detection algorithms
- OCR parsing functions
- GTO calculations
- State management logic

### Integration Tests
- WebSocket communication
- End-to-end frame processing
- Frontend-backend integration

### Performance Tests
- Frame processing latency
- WebSocket throughput
- Memory usage
- CPU utilization

## Deployment Architecture

### Development
```
[Phone] ←WiFi→ [Laptop Frontend:3000 + Backend:8000]
```

### Production
```
[Phone] ←4G/5G→ [CDN (Frontend)] ←→ [Load Balancer] ←→ [Backend Servers]
                                            ↓
                                     [Redis Cache]
```

## Future Architecture Enhancements

### Phase 2
- Add Redis for state persistence
- Implement WebRTC for lower latency
- Use GPU inference for real-time processing
- Add PostgreSQL for hand history logging

### Phase 3
- Microservices split (CV, OCR, GTO as separate services)
- Message queue (RabbitMQ/Kafka) for async processing
- Multi-table support (parallel processing)
- Real-time training from user feedback

### Phase 4
- Kubernetes deployment
- Auto-scaling based on load
- ML model versioning and A/B testing
- Real-time analytics dashboard

## Tech Debt & Refactoring Needs

### Known Issues
1. No proper error recovery in WebSocket
2. Simplified GTO logic (not production-ready)
3. Color detection may fail with non-standard themes
4. No frame buffering for smooth processing
5. Hard-coded thresholds need tuning

### Refactoring Priorities
1. Extract configuration to environment variables
2. Add comprehensive logging
3. Implement retry logic for failed operations
4. Create abstract base classes for detectors
5. Add dependency injection for testability

## Monitoring & Observability

### Metrics to Track
- Frame processing time
- Detection accuracy
- WebSocket latency
- Error rates
- User sessions
- Recommendations per minute

### Logging Strategy
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for request tracing
- Performance metrics in logs

### Alerting
- High error rates
- Increased latency
- Service downtime
- Resource exhaustion

## Conclusion

This architecture provides a solid foundation for MVP while maintaining extensibility for future enhancements. The modular design allows for easy iteration and improvement of individual components without affecting the overall system.
