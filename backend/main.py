"""
Main FastAPI server for Poker GTO Vision
Hybrid AI System: Gemini (vision) → GPT-4o-mini (poker logic)
"""

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from gemini_analyzer import GeminiDataExtractor
from gpt_poker_logic import GPTPokerLogic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Poker GTO Vision Backend - Hybrid AI")

# CORS middleware for frontend communication
allowed_origins = [
    "https://lelabubu.ca",
    "https://www.lelabubu.ca",
    "https://poker-gto-vision-frontend.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

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

# Initialize hybrid AI system
gemini_extractor = GeminiDataExtractor()
gpt_logic = GPTPokerLogic()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "Poker GTO Vision Backend - Hybrid AI",
        "version": "3.0.0",
        "vision": "Gemini 2.0 Flash Experimental",
        "logic": "GPT-4o-mini"
    }


@app.post("/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    position: str = Form("BTN")
):
    """
    Analyze poker table image using Hybrid AI:
    1. Gemini extracts visual data from image
    2. GPT-4o-mini makes poker decision based on data
    
    Returns: 5 decision metrics + action recommendation
    """
    try:
        logger.info(f"📸 Received image: {image.filename}, position: {position}")
        
        # Read image data
        image_data = await image.read()
        
        # STEP 1: Gemini extracts visual data
        logger.info(f"👁️  Step 1: Gemini extracting visual data...")
        extraction_result = gemini_extractor.extract_data(image_data, hero_position=position)
        
        if not extraction_result.get("success"):
            return {
                "success": False,
                "error": extraction_result.get("error", "Data extraction failed"),
                "message": "Failed to extract poker table data. Please try again."
            }
        
        extracted_data = extraction_result["extracted_data"]
        logger.info(f"✅ Gemini extracted: {len(extracted_data.get('villain_positions', {}))} villains, {extracted_data.get('street', 'unknown')} street")
        
        # Check if hero's cards were extracted
        hero_cards = extracted_data.get("hero_cards", [])
        if not hero_cards or len(hero_cards) == 0:
            return {
                "success": False,
                "error": "Hero's cards not detected",
                "message": "❌ Failed to identify your hole cards. Please capture again with cards clearly visible."
            }
        
        # Check if it's hero's turn
        if not extracted_data.get("is_hero_turn", False):
            return {
                "success": False,
                "hero_turn": False,
                "message": "Not hero's turn detected. Capture when action is on you."
            }
        
        # STEP 2: GPT makes poker decision
        logger.info(f"🧠 Step 2: GPT-4o-mini making decision...")
        decision_result = gpt_logic.make_decision(extracted_data)
        
        if not decision_result.get("success"):
            return {
                "success": False,
                "error": decision_result.get("error", "Decision failed"),
                "message": "Failed to make poker decision. Please try again."
            }
        
        decision = decision_result["decision"]
        recommendation = decision["recommendation"]
        
        logger.info(f"✅ GPT decision: {recommendation['action']}")
        
        # Format for frontend (5 metrics + action)
        action = recommendation.get("action", "Unknown")
        raise_amount = recommendation.get("raise_amount_dollars", "N/A")
        
        if action in ["Raise", "Bet"] and raise_amount != "N/A":
            action_display = f"{action} {raise_amount}"
        else:
            action_display = action
        
        # Calculate pot size in BB (for display)
        try:
            pot_dollars = float(extracted_data.get("pot_size_dollars", "$0").replace("$", ""))
            # Assume 0.50 BB for now, or extract from context
            pot_bb = pot_dollars / 0.50
        except:
            pot_bb = 0
        
        return {
            "success": True,
            "hero_turn": True,
            
            # Main display - 5 decision metrics
            "recommendation": {
                "action": action_display,
                "pot_odds": recommendation.get("pot_odds", "N/A"),
                "hand_equity": recommendation.get("hand_equity", "N/A"),
                "implied_odds": recommendation.get("implied_odds", "N/A"),
                "fold_equity": recommendation.get("fold_equity", "N/A"),
                "expected_value": recommendation.get("expected_value", "N/A"),
                "pot_size": f"{pot_bb:.1f} BB",
                "position": extracted_data.get("hero_position", position)
            },
            
            # Detailed info for side panel
            "detailed_info": {
                "game_state": {
                    "street": extracted_data.get("street", "unknown"),
                    "pot_dollars": extracted_data.get("pot_size_dollars", "N/A"),
                    "hero_cards": extracted_data.get("hero_cards", []),
                    "board_cards": extracted_data.get("board_cards", [])
                },
                "players": {
                    pos: {
                        "name": data.get("player_name", "Unknown"),
                        "position": pos
                    }
                    for pos, data in extracted_data.get("villain_positions", {}).items()
                },
                "pot_odds": recommendation.get("pot_odds", {}),
                "hand_equity": recommendation.get("hand_equity", {}),
                "implied_odds": recommendation.get("implied_odds", {}),
                "fold_equity": recommendation.get("fold_equity", {}),
                "expected_value": recommendation.get("expected_value", {}),
                "optimal_play": recommendation.get("optimal_play", ""),
                "action_history": extracted_data.get("betting_history", [])
            },
            
            # Raw data for debugging (optional)
            "debug": {
                "extracted_data": extracted_data,
                "gpt_decision": decision
            }
        }
            
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}", exc_info=True)
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
