"""
Gemini-powered poker table analyzer
Uses Google's Gemini Flash 2.0 Experimental for comprehensive poker analysis
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
POKER_ANALYSIS_PROMPT = """You are an expert poker mathematician specializing in GTO (Game Theory Optimal) analysis.

Analyze this poker table screenshot from GGPoker and provide a comprehensive mathematical analysis.

Your response MUST be valid JSON with this exact structure:

{
  "game_info": {
    "pot_size_bb": <number>,
    "pot_size_dollars": "<string>",
    "hero_position": "<BTN|SB|BB|UTG|MP|CO>",
    "street": "<preflop|flop|turn|river>",
    "is_hero_turn": <boolean>
  },
  "recommendation": {
    "action": "<Fold|Call|Check|Raise|Bet>",
    "raise_amount_dollars": "<exact dollar amount like '$4.50' or 'N/A' if not raising>",
    "pot_odds": "<ratio like 3:1 or percentage like 25%>",
    "hand_equity": "<percentage like 45%>",
    "implied_odds": "<ratio like 5:1 or 'High/Medium/Low'>",
    "fold_equity": "<percentage like 35%>",
    "expected_value": "<dollar amount like '+$2.10' or '-$1.50'>",
    "reasoning": "<brief 1-2 sentence explanation based on the 5 metrics>"
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

1. **DEALER BUTTON IDENTIFICATION**:
   - Look for a YELLOW circular marker with the letter "D" next to a player's name
   - This "D" button appears on the right side of the player's seat card
   - It's a small yellow/gold circle - this is THE dealer button
   
2. **HERO IDENTIFICATION**:
   - Hero is ALWAYS at the BOTTOM-CENTER position of the table
   - Hero's cards are visible at the bottom (e.g., showing pocket cards like JJ, 77, etc.)
   - Hero's action buttons (Fold, Call, Raise) appear at the bottom when it's their turn
   
3. **POSITION CALCULATION** (Count clockwise from dealer button):
   - Start at the player WITH the "D" button marker = Button (BTN)
   - Move clockwise (to the left looking at the table from hero's perspective):
     * Button (BTN) = Has the "D" marker
     * Small Blind (SB) = 1 seat clockwise from button
     * Big Blind (BB) = 2 seats clockwise from button
     * Under The Gun (UTG) = 3 seats clockwise from button
     * Middle Position (MP) = 4 seats clockwise from button
     * Cutoff (CO) = 5 seats clockwise from button
   
4. **STREET IDENTIFICATION**:
   - No community cards = preflop
   - 3 cards on board = flop
   - 4 cards = turn
   - 5 cards = river

5. **CRITICAL: ACCURATE HAND READING** (DO NOT HALLUCINATE):
   
   **Read Hero's Exact Cards:**
   - Identify BOTH hero's cards precisely (rank AND suit)
   - Example: A♠ Q♠ = Ace of Spades, Queen of Spades
   
   **Read Board Cards:**
   - Identify ALL board cards precisely (rank AND suit)
   - Example: 8♦ 6♦ 9♥ = Eight of Diamonds, Six of Diamonds, Nine of Hearts
   
   **Flush Draws - VERIFY SUITS:**
   - Flush draw = 4 cards of SAME suit (e.g., hero has 2 spades + 2 spades on board)
   - If hero has spades and board has diamonds: NO FLUSH DRAW
   - DO NOT assume flush draws - COUNT the suits!
   
   **Straight Draws - VERIFY CONNECTIVITY:**
   - Open-ended = 4 cards in sequence, missing either end (e.g., 6789 needs 5 or T)
   - Gutshot = 4 cards with 1 gap (e.g., 5689 needs 7)
   - For AQ on 689 board: NO straight draw (AQ doesn't connect)
   - DO NOT assume straight draws - CHECK if cards actually connect!
   
   **RULE: If you can't see a clear draw, DON'T mention it in reasoning!**

6. **POST-FLOP DECISION MAKING** (FLOP/TURN/RIVER):
   
   Your decision MUST be based SOLELY on these 5 mathematical metrics:
   
   **A. POT ODDS**:
   - Formula: (Amount to call) / (Pot after you call)
   - Express as ratio (3:1) or percentage (25%)
   - Critical for call/fold decisions
   
   **B. HAND EQUITY**:
   - Calculate hero's exact winning percentage against villain's range
   - Consider:
     * Position (tighter from early, wider from late)
     * Action (aggressor has stronger range)
     * Board texture (remove unlikely hands)
   - Express as percentage (e.g., "45%")
   
   **C. IMPLIED ODDS**:
   - Estimate additional chips you can win on future streets if you hit
   - Factors:
     * Remaining stack depths
     * Board texture (wet boards = lower implied odds)
     * Villain's playing style (loose = higher implied odds)
   - Express as ratio (e.g., "5:1") or description ("High/Medium/Low")
   
   **D. FOLD EQUITY**:
   - Estimate % chance villain folds to a bet/raise
   - Factors:
     * Villain's VPIP (tight players fold more)
     * Board texture (scary boards = more folds)
     * Bet sizing (larger bets = more folds)
     * Pot size (small pots = easier folds)
   - Express as percentage (e.g., "35%")
   
   **E. EXPECTED VALUE (EV)**:
   - For Call: EV = (Hand Equity × Pot) - Call Amount + (Implied Odds Factor)
   - For Bet/Raise: EV = (Fold Equity × Current Pot) + ((1 - Fold Equity) × ((Hand Equity × Total Pot) - Bet Amount))
   - Express in dollars (e.g., "+$2.10" or "-$0.75")
   
   **DECISION LOGIC POST-FLOP:**
   - If Pot Odds < Hand Equity + Implied Odds → CALL is profitable
   - If EV(Bet/Raise) > EV(Call) → BET/RAISE is optimal
   - If all EVs are negative → FOLD
   - Fold Equity justifies bluffs when combined with some equity
   
7. **PREFLOP DECISION MAKING**:
   - Preflop can use broader strategic considerations
   - Position, ranges, and GTO principles apply
   - But still calculate the 5 metrics where applicable

8. **RAISE SIZING**:
   - If recommending Raise/Bet, provide EXACT dollar amount (e.g., "$4.50")
   - Sizing guidelines:
     * Value bets: 60-75% pot
     * Bluffs: 50-60% pot
     * 3-bets preflop: 3-4x initial raise

REMEMBER FOR POST-FLOP: 
- Base your decision PURELY on the 5 metrics
- No subjective reads or "feel" - only mathematics
- Calculate each metric precisely
- Show your work in the reasoning

Return ONLY valid JSON, no markdown, no extra text."""


class GeminiPokerAnalyzer:
    """Poker table analyzer using Gemini vision"""
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini 2.0 Flash Experimental analyzer initialized")
    
    def _get_relative_positions(self, hero_position: str) -> str:
        """Generate a position map relative to hero's position"""
        positions = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
        screen_positions = [
            "Bottom-Center",  # Hero
            "Bottom-Left", "Top-Left", "Top-Center", "Top-Right", "Bottom-Right"
        ]
        
        hero_idx = positions.index(hero_position)
        mapping_lines = []
        for i, screen_pos in enumerate(screen_positions):
            pos_idx = (hero_idx + i) % 6
            actual_position = positions[pos_idx]
            if i == 0:
                mapping_lines.append(f"- {screen_pos}: {actual_position} (HERO - YOU)")
            else:
                mapping_lines.append(f"- {screen_pos}: {actual_position}")
        
        return "\n".join(mapping_lines)
    
    def analyze_poker_table(self, image_data: bytes, hero_position: str = "BTN") -> Dict[str, Any]:
        """Analyze poker table image using Gemini"""
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }
        
        try:
            logger.info(f"🤖 Sending image to Gemini for analysis... Hero position: {hero_position}")
            
            image = Image.open(BytesIO(image_data))
            position_map = self._get_relative_positions(hero_position)
            
            position_prompt = f"""{POKER_ANALYSIS_PROMPT}

CRITICAL POSITION INFORMATION:
Hero is seated at {hero_position} position (bottom-center of screen).

RELATIVE POSITIONS FROM HERO:
{position_map}

USE THIS MAPPING: Use the screen position to determine poker positions based on the mapping above."""
            
            response = self.model.generate_content([position_prompt, image])
            analysis_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if analysis_text.startswith("```json"):
                analysis_text = analysis_text[7:]
            if analysis_text.startswith("```"):
                analysis_text = analysis_text[3:]
            if analysis_text.endswith("```"):
                analysis_text = analysis_text[:-3]
            
            analysis_text = analysis_text.strip()
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
        """Format Gemini analysis for frontend display with 5 metrics"""
        try:
            game_info = analysis.get("game_info", {})
            recommendation = analysis.get("recommendation", {})
            detailed = analysis.get("detailed_analysis", {})
            
            action = recommendation.get("action", "Unknown")
            raise_amount = recommendation.get("raise_amount_dollars", "N/A")
            
            if action in ["Raise", "Bet"] and raise_amount != "N/A":
                action_display = f"{action} {raise_amount}"
            else:
                action_display = action
            
            return {
                "success": True,
                "hero_turn": game_info.get("is_hero_turn", False),
                
                # Main display - 5 decision metrics
                "recommendation": {
                    "action": action_display,
                    "pot_odds": recommendation.get("pot_odds", "N/A"),
                    "hand_equity": recommendation.get("hand_equity", "N/A"),
                    "implied_odds": recommendation.get("implied_odds", "N/A"),
                    "fold_equity": recommendation.get("fold_equity", "N/A"),
                    "expected_value": recommendation.get("expected_value", "N/A"),
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
