"""
Main FastAPI server for Poker GTO Vision
Powered by Gemini Flash 2.5 for AI-driven poker analysis
"""

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from gemini_analyzer import GeminiPokerAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Poker GTO Vision Backend - Gemini Powered")

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

# Initialize Gemini analyzer
analyzer = GeminiPokerAnalyzer()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "Poker GTO Vision Backend - Gemini Powered",
        "version": "2.0.0",
        "model": "Gemini Flash 2.5"
    }


@app.post("/analyze")
async def analyze_image(image: UploadFile = File(...)):
    """
    Analyze poker table image using Gemini AI
    Returns: Main display data + detailed side panel info
    """
    try:
        logger.info(f"📸 Received image: {image.filename}")
        
        # Read image data
        image_data = await image.read()
        
        logger.info(f"🖼️  Sending to Gemini for analysis...")
        
        # Analyze with Gemini
        result = analyzer.analyze_poker_table(image_data)
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Analysis failed"),
                "message": "Failed to analyze poker table. Please try again."
            }
        
        # Format for frontend
        formatted = analyzer.format_for_frontend(result["analysis"])
        
        logger.info(f"✅ Analysis complete: {formatted['recommendation']['action']}")
        
        return formatted
            
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
