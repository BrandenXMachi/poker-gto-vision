"""
Main FastAPI server for Poker Vision
Three modes: Preflop, Flop, and Turn/River
"""

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from flop_gto_analyzer import FlopGTOAnalyzer
from preflop_gto_analyzer import PreflopGTOAnalyzer
from turn_river_analyzer import TurnRiverAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Poker Vision Backend")

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

# Initialize AI analyzers
flop_analyzer = FlopGTOAnalyzer()
preflop_analyzer = PreflopGTOAnalyzer()
tr_analyzer = TurnRiverAnalyzer()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "Poker Vision Backend",
        "version": "6.0.0",
        "modes": {
            "preflop": "Preflop Mode - GTO ranges + structured preflop decisions",
            "flop": "Flop Mode - Hand evaluator + position-aware flop strategy",
            "tr": "Turn/River Mode - Mathematical pot odds + equity analysis"
        }
    }


@app.post("/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    position: str = Form(None),
    blinds: str = Form("0.02/0.05"),
    ai_mode: str = Form("flash"),
    # Flop Mode specific parameters
    hero_position: str = Form(None),
    villain_position: str = Form(None),
    villain_action: str = Form(None),
    # Preflop Mode specific parameters
    is_open_raise: str = Form("false"),
    # T/R Mode context from Flop (optional)
    hero_cards: str = Form(None),
    flop_cards: str = Form(None),
    flop_action: str = Form(None)
):
    """
    Analyze poker table image using selected mode:
    - "preflop": Preflop GTO analysis with optimized ranges
    - "flop": Flop analysis with hand evaluator and position-aware strategy
    - "tr": Turn/River mathematical analysis with pot odds and equity
    
    Returns: Complete poker analysis with recommendation
    """
    try:
        logger.info(f"📸 Received image: {image.filename}, position: {position}, blinds: {blinds}, mode: {ai_mode}")
        
        # Read image data
        image_data = await image.read()
        
        # Route to appropriate analyzer based on mode
        if ai_mode == "flop":
            # FLOP MODE - Flop-only GTO analysis with preflop context
            logger.info(f"🎴 Using Flop mode - Hero: {hero_position}, Villain: {villain_position}, Preflop: {villain_action}")
            result = flop_analyzer.analyze(
                image_data,
                hero_position=hero_position,  # "IP" or "OOP"
                preflop_action=villain_action,  # "villain_called", "villain_3bet", "villain_opened", "villain_4bet"
                villain_position=villain_position,  # "UTG", "MP", "CO", "BTN", "SB", "BB"
                blinds=blinds
            )
            
        elif ai_mode == "preflop":
            # PREFLOP MODE - Gemini vision + Custom GTO algorithm
            is_open = is_open_raise.lower() == "true"
            logger.info(f"🎯 Using Preflop mode - Hero: {position}, Villain: {villain_position}, Open Raise: {is_open}, Blinds: {blinds}")
            result = preflop_analyzer.analyze(
                image_data,
                position=position,
                villain_position=villain_position if not is_open else None,
                blinds=blinds,
                is_open_raise=is_open
            )
            
        elif ai_mode == "tr":
            # TURN/RIVER MODE - Mathematical pot odds analysis
            # Parse context if provided from Flop mode
            import json
            hero_cards_list = None
            flop_cards_list = None
            
            if hero_cards:
                try:
                    hero_cards_list = json.loads(hero_cards)
                    logger.info(f"✅ Received hero cards from flop: {hero_cards_list}")
                except:
                    pass
            
            if flop_cards:
                try:
                    flop_cards_list = json.loads(flop_cards)
                    logger.info(f"✅ Received flop cards: {flop_cards_list}")
                except:
                    pass
            
            logger.info(f"📊 Using Turn/River mode - Blinds: {blinds}, Has Context: {hero_cards_list is not None}")
            result = tr_analyzer.analyze(
                image_data,
                blinds=blinds,
                hero_cards=hero_cards_list,
                flop_cards=flop_cards_list,
                hero_position=hero_position,
                villain_position=villain_position,
                flop_action=flop_action
            )
            
        else:
            return {
                "success": False,
                "error": f"Invalid mode: {ai_mode}. Use 'preflop', 'flop', or 'tr'",
                "message": "Invalid analysis mode selected."
            }
        
        # Check if analysis was successful
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Analysis failed"),
                "message": result.get("error", "Failed to analyze. Please try again.")
            }
        
        extracted_data = result.get("extracted_data", {})
        recommendation = result.get("recommendation", {})
        
        # Format for frontend
        action = recommendation.get("action", "Unknown")
        reasoning = recommendation.get("reasoning", "")
        
        # Calculate pot size in BB (for display)
        try:
            pot_dollars = float(extracted_data.get("pot_size_dollars", "$0").replace("$", ""))
            # Parse blinds to get BB value
            bb_value = float(blinds.split('/')[1])
            pot_bb = pot_dollars / bb_value
        except:
            pot_bb = 0
        
        # Unified response format for both modes
        return {
            "success": True,
            "hero_turn": True,
            "ai_mode": ai_mode,
            
            # Extracted data at root level for frontend access
            "extracted_data": extracted_data,
            
            # Main display - 5 decision metrics
            "recommendation": {
                "action": action,
                "pot_odds": recommendation.get("pot_odds", {}).get("value", recommendation.get("pot_odds", "N/A")) if isinstance(recommendation.get("pot_odds"), dict) else recommendation.get("pot_odds", "N/A"),
                "hand_equity": recommendation.get("hand_equity", {}).get("value", recommendation.get("hand_equity", "N/A")) if isinstance(recommendation.get("hand_equity"), dict) else recommendation.get("hand_equity", "N/A"),
                "implied_odds": recommendation.get("implied_odds", {}).get("value", recommendation.get("implied_odds", "N/A")) if isinstance(recommendation.get("implied_odds"), dict) else recommendation.get("implied_odds", "N/A"),
                "fold_equity": recommendation.get("fold_equity", {}).get("value", recommendation.get("fold_equity", "N/A")) if isinstance(recommendation.get("fold_equity"), dict) else recommendation.get("fold_equity", "N/A"),
                "expected_value": recommendation.get("expected_value", {}).get("value", recommendation.get("expected_value", "N/A")) if isinstance(recommendation.get("expected_value"), dict) else recommendation.get("expected_value", "N/A"),
                "pot_size": f"{pot_bb:.1f} BB",
                "position": extracted_data.get("hero_position", position),
                "reasoning": reasoning
            },
            
            # Detailed info for side panel
            "detailed_info": {
                "game_state": {
                    "street": extracted_data.get("street", "unknown"),
                    "pot_dollars": extracted_data.get("pot_size_dollars", "N/A"),
                    "pot_bb": extracted_data.get("pot_size_bb", f"{pot_bb:.1f} BB"),
                    "hero_cards": extracted_data.get("hero_cards", []),
                    "board_cards": extracted_data.get("board_cards", [])
                },
                "players": {
                    pos: {
                        "name": data.get("player_name", "Unknown"),
                        "position": pos,
                        "stack": data.get("stack", data.get("stack_bb", "N/A")),
                        "vpip": data.get("vpip", "N/A"),
                        "vpip_category": data.get("vpip_category", "unknown")
                    }
                    for pos, data in extracted_data.get("villain_positions", {}).items()
                    if not data.get("has_folded", False)
                },
                "pot_odds": recommendation.get("pot_odds", {}),
                "hand_equity": recommendation.get("hand_equity", {}),
                "implied_odds": recommendation.get("implied_odds", {}),
                "fold_equity": recommendation.get("fold_equity", {}),
                "expected_value": recommendation.get("expected_value", {}),
                "optimal_play": recommendation.get("optimal_play", reasoning),
                "gto_frequency": recommendation.get("gto_frequency", ""),
                "range_advantage": recommendation.get("range_advantage", ""),
                "action_history": extracted_data.get("betting_history", [])
            },
            
            # Raw data for debugging (optional)
            "debug": {
                "extracted_data": extracted_data,
                "ai_mode": ai_mode
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
