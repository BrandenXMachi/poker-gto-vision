"""
Main FastAPI server for Poker GTO Vision
Handles WebSocket connections and frame processing
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time frame processing"""
    await websocket.accept()
    logger.info("Client connected")
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "message": "Connected to Poker GTO Vision server"
        })
        
        while True:
            # Receive frame from client
            data = await websocket.receive_bytes()
            
            # Process frame in background to avoid blocking
            asyncio.create_task(process_frame(websocket, data))
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


async def process_frame(websocket: WebSocket, frame_data: bytes):
    """Process a single frame and send recommendation if hero's turn detected"""
    try:
        # Convert bytes to image
        image = Image.open(BytesIO(frame_data))
        frame = np.array(image)
        
        # Detect poker UI elements
        detections = detector.detect(frame)
        
        # Update game state
        game_state.update(detections)
        
        # Check if it's hero's turn
        if game_state.is_hero_turn():
            # Get GTO recommendation
            recommendation = solver.get_recommendation(game_state)
            
            # Send recommendation to client
            await websocket.send_json({
                "type": "recommendation",
                "recommendation": {
                    "action": recommendation["action"],
                    "pot_size": recommendation.get("pot_size"),
                    "ev": recommendation.get("ev"),
                    "reasoning": recommendation.get("reasoning")
                }
            })
            
            # Reset hero turn flag to avoid duplicate recommendations
            game_state.reset_hero_turn()
            
    except Exception as e:
        logger.error(f"Frame processing error: {e}")
        # Don't send error to client, just continue processing


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
