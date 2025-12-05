"""
Gemini-powered poker table analyzer
Uses Google's Gemini Flash 2.5 for comprehensive poker analysis
"""

import os
import base64
import json
import logging
from typing import Dict, Any
import google.generativeai as genai
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Configure Gemini (will be checked on first use)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API key configured")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set - add it to environment variables on Render")

# Poker analysis prompt
POKER_ANALYSIS_PROMPT = """You are an expert poker GTO (Game Theory Optimal) advisor analyzing a poker table screenshot from GGPoker.

Analyze this poker table image and provide a comprehensive analysis in JSON format.

Your response MUST be valid JSON with this exact structure:

{
  "game_info": {
    "pot_size_bb": <number>,
    "pot_size_dollars": "<string>",
    "hero_position": "<BTN|SB|BB|UTG|MP|CO>",
    "street": "<preflop|flop|turn|river>",
    "is_hero_turn": <boolean>
  },
  "pot_odds": "<ratio like 3:1>",
  "hand_equity": "<percentage like 45%>",
  "recommendation": {
    "action": "<Fold|Call|Raise>",
    "reasoning": "<brief explanation>"
  },
  "detailed_analysis": {
    "board_cards": [<list of cards or empty>],
    "stack_sizes": {<position: stackBB>},
    "action_history": [<list of actions>],
    "range_analysis": "<detailed range discussion>",
    "ev_calculation": "<EV breakdown>",
    "alternative_lines": [<other viable options>]
  }
}

CRITICAL ANALYSIS GUIDELINES:

1. **DEALER BUTTON IDENTIFICATION** (MOST IMPORTANT):
   - Look for a YELLOW circular marker with the letter "D" next to a player's name
   - This "D" button appears on the right side of the player's seat card
   - It's a small yellow/gold circle - this is THE dealer button
   - Example: If you see "D" next to player "ag3nt911", that player IS the dealer/button
   
2. **HERO IDENTIFICATION**:
   - Hero is ALWAYS at the BOTTOM-CENTER position of the table
   - Hero's cards are visible at the bottom (e.g., showing pocket cards like JJ, 77, etc.)
   - Hero's action buttons (Fold, Call, Raise) appear at the bottom when it's their turn
   - Hero's username is at the bottom-center seat
   
3. **POSITION CALCULATION** (Count clockwise from dealer button):
   - Start at the player WITH the "D" button marker = Button (BTN)
   - Move clockwise (to the left looking at the table from hero's perspective):
     * Button (BTN) = Has the "D" marker
     * Small Blind (SB) = 1 seat clockwise from button
     * Big Blind (BB) = 2 seats clockwise from button
     * Under The Gun (UTG) = 3 seats clockwise from button (first to act preflop)
     * Middle Position (MP) = 4 seats clockwise from button
     * Cutoff (CO) = 5 seats clockwise from button (1 seat before button)
   
4. **6-Max Table Layout**:
   - Seats are arranged in a circle: Top-Center, Top-Right, Bottom-Right, Bottom-Center (HERO), Bottom-Left, Top-Left
   - Count positions clockwise starting from whoever has the "D" button
   
5. **Pot Size**: 
   - Look for "Total Pot : $X.XX" text on the table
   - Convert to big blinds by dividing by BB amount
   
6. **Street**: 
   - No community cards = preflop
   - 3 cards on board = flop
   - 4 cards = turn
   - 5 cards = river
   
7. **Hero's Turn**: 
   - Check if action buttons (Fold, Call, Raise/Bet) are visible at bottom
   - Check if there's a timer or highlight on hero's seat
   
8. **Pot Odds & Equity**:
   - Calculate pot odds: (amount to call) : (current pot + amount to call)
   - Estimate equity based on position, action, and visible cards
   
9. **GTO Recommendation**: 
   - Provide theoretically optimal play based on position, pot odds, and situation
   - Consider: position strength, pot odds, likely ranges, stack depths

REMEMBER: The "D" button marker is THE KEY to determining position correctly!

Return ONLY valid JSON, no markdown, no extra text."""


class GeminiPokerAnalyzer:
    """Poker table analyzer using Gemini vision"""
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini analyzer initialized")
    
    def analyze_poker_table(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze poker table image using Gemini
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with analysis results
        """
        # Check if API key is configured
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured. Please add it to Render environment variables."
            }
        
        try:
            logger.info("🤖 Sending image to Gemini for analysis...")
            
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Generate analysis
            response = self.model.generate_content([
                POKER_ANALYSIS_PROMPT,
                image
            ])
            
            # Parse JSON response
            analysis_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if analysis_text.startswith("```json"):
                analysis_text = analysis_text[7:]
            if analysis_text.startswith("```"):
                analysis_text = analysis_text[3:]
            if analysis_text.endswith("```"):
                analysis_text = analysis_text[:-3]
            
            analysis_text = analysis_text.strip()
            
            # Parse JSON
            analysis = json.loads(analysis_text)
            
            logger.info(f"✅ Gemini analysis complete: {analysis['recommendation']['action']}")
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {response.text[:500]}")
            return {
                "success": False,
                "error": "Failed to parse analysis response",
                "raw_response": response.text[:500]
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_for_frontend(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Gemini analysis for frontend display
        
        Returns simplified view for main UI and detailed side panel data
        """
        try:
            game_info = analysis.get("game_info", {})
            recommendation = analysis.get("recommendation", {})
            detailed = analysis.get("detailed_analysis", {})
            
            return {
                "success": True,
                "hero_turn": game_info.get("is_hero_turn", False),
                
                # Main display (pot odds, equity, action)
                "recommendation": {
                    "action": recommendation.get("action", "Unknown"),
                    "pot_odds": analysis.get("pot_odds", "N/A"),
                    "hand_equity": analysis.get("hand_equity", "N/A"),
                    "pot_size": f"{game_info.get('pot_size_bb', 0)} BB",
                    "position": game_info.get("hero_position", "Unknown")
                },
                
                # Side panel (detailed info)
                "detailed_info": {
                    "game_state": {
                        "street": game_info.get("street", "preflop"),
                        "pot_dollars": game_info.get("pot_size_dollars", "N/A"),
                        "board_cards": detailed.get("board_cards", [])
                    },
                    "reasoning": recommendation.get("reasoning", ""),
                    "range_analysis": detailed.get("range_analysis", ""),
                    "ev_calculation": detailed.get("ev_calculation", ""),
                    "action_history": detailed.get("action_history", []),
                    "stack_sizes": detailed.get("stack_sizes", {}),
                    "alternative_lines": detailed.get("alternative_lines", [])
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Format error: {e}")
            return {
                "success": False,
                "error": "Failed to format analysis"
            }
