"""
Main FastAPI server for Poker GTO Vision
Handles WebSocket connections and frame processing
"""

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from io import BytesIO
from PIL import Image
import numpy as np

from cv.detector import PokerDetector
from game.state import GameStateManager
from solver.gto import GTOSolver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Poker GTO Vision Backend")

# CORS middleware for frontend communication
import os

# Allow frontend domain and localhost for development
allowed_origins = [
    "https://lelabubu.ca",
    "https://www.lelabubu.ca",
    "https://poker-gto-vision-frontend.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Add Render frontend URL if available
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
detector = PokerDetector()
game_state = GameStateManager()
solver = GTOSolver()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "Poker GTO Vision Backend Running", "version": "1.0.0"}


@app.post("/analyze")
async def analyze_image(image: UploadFile = File(...)):
    """
    Analyze a poker table image and return GTO recommendation
    """
    try:
        logger.info(f"📸 Received image: {image.filename}")
        
        # Read image data
        image_data = await image.read()
        
        # Convert to PIL Image
        pil_image = Image.open(BytesIO(image_data))
        frame = np.array(pil_image)
        
        logger.info(f"🖼️  Image size: {frame.shape}")
        
        # Detect poker UI elements
        detections = detector.detect(frame)
        
        # Update game state
        game_state.update(detections)
        
        # Check if it's hero's turn
        if game_state.is_hero_turn():
            # Get GTO recommendation
            recommendation = solver.get_recommendation(game_state)
            
            logger.info(f"✅ Hero turn detected! Recommendation: {recommendation['action']}")
            
            return {
                "success": True,
                "hero_turn": True,
                "recommendation": {
                    "action": recommendation["action"],
                    "pot_size": recommendation.get("pot_size"),
                    "ev": recommendation.get("ev"),
                    "reasoning": recommendation.get("reasoning")
                },
                "detections": {
                    "buttons_visible": detections.get("buttons_visible"),
                    "timer_active": detections.get("timer_active")
                }
            }
        else:
            logger.info("ℹ️  Not hero's turn")
            return {
                "success": True,
                "hero_turn": False,
                "message": "Not your turn yet. Capture when action is on you.",
                "detections": {
                    "buttons_visible": detections.get("buttons_visible"),
                    "timer_active": detections.get("timer_active")
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to analyze image. Make sure poker table is clearly visible."
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
