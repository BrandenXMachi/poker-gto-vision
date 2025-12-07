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
POKER_ANALYSIS_PROMPT = """You are an expert poker GTO (Game Theory Optimal) advisor with deep understanding of game theory, exploitative play, and hand reading.

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
    "action": "<Fold|Call|Check|Raise>",
    "raise_amount_dollars": "<exact dollar amount like '$4.50' or 'N/A' if not raising>",
    "pot_odds": "<ratio like 3:1 or percentage like 25%>",
    "equity_vs_range": "<percentage like 45%>",
    "fold_equity": "<percentage like 35%>",
    "expected_value": "<dollar amount like '+$2.10' or '-$1.50'>",
    "reasoning": "<brief 1-2 sentence explanation>"
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
   
8. **INFER GAME HISTORY & ACTION**:
   From the snapshot, deduce:
   - **Who is the aggressor**: Look at bet sizes, who has chips in front of them, position
   - **Action sequence**: Infer if there was a raise, 3-bet, 4-bet based on pot size and stack changes
   - **Bet sizes**: Calculate from visible chips and pot
   - **Likely holdings**: Based on position, action, and bet sizing

9. **VPIP EXPLOITATION**:
   - Look for VPIP percentage ABOVE each player's name (small text)
   - VPIP > 35% = Loose player (wider range, exploit with value betting)
   - VPIP 20-35% = Standard player (balanced range)
   - VPIP < 20% = Tight player (narrow range, can bluff more)
   - Adjust your range construction and fold equity estimates accordingly

10. **BOARD TEXTURE ANALYSIS**:
   - Dry boards (K♠72♦) = Less fold equity, value-bet heavy
   - Wet boards (JT9♠♠) = More fold equity, can semi-bluff draws
   - Coordinated boards favor the aggressor's range
   - Static vs dynamic boards affect equity realization

11. **CALCULATE THE 4 DECISION METRICS**:

   **A. Pot Odds**:
   - Formula: (Amount to call) / (Pot after you call)
   - Express as ratio (3:1) or percentage (25%)
   
   **B. Equity vs Villain's Range**:
   - Construct villain's likely range based on:
     * Position (tighter from early, wider from late)
     * Action (aggressor has stronger range)
     * VPIP stats (adjust range width)
     * Board texture (remove unlikely hands)
   - Calculate hero's equity against this range
   - Consider blockers (hero's cards that reduce villain's combos)
   
   **C. Fold Equity**:
   - Estimate % chance villain folds to a raise
   - Factors: Villain's VPIP, board texture, pot size, stack depth
   - Tight players (low VPIP) fold more to aggression
   - Smaller pots = easier to fold
   
   **D. Expected Value (EV)**:
   - For Call: EV = (Equity × Pot) - Call Amount
   - For Raise: EV = (Fold Equity × Current Pot) + ((1 - Fold Equity) × ((Equity × Total Pot) - Raise Amount))
   - Express in dollars (e.g., "+$2.10" or "-$0.75")

12. **RAISE SIZING**:
   - If recommending Raise, provide EXACT dollar amount (e.g., "$4.50")
   - Sizing guidelines:
     * Value raises: 2.5-3x pot
     * Bluff raises: 0.5-0.75x pot
     * 3-bets: 3-4x initial raise
   - Consider stack-to-pot ratio (SPR) for all-in decisions

REMEMBER: 
- Use visible clues to reconstruct the hand history
- Let VPIP stats guide your exploitation strategy
- Calculate all 4 metrics with precision
- Provide exact raise amounts in dollars

Return ONLY valid JSON, no markdown, no extra text."""


class GeminiPokerAnalyzer:
    """Poker table analyzer using Gemini vision"""
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini analyzer initialized")
    
    def _get_relative_positions(self, hero_position: str) -> str:
        """
        Generate a position map relative to hero's position
        
        6-max table screen positions (from hero's view):
        - Top-Left, Top-Center, Top-Right
        - Bottom-Left, Bottom-Center (HERO), Bottom-Right
        
        Positions move clockwise: BTN -> SB -> BB -> UTG -> MP -> CO
        """
        # Define all positions in clockwise order
        positions = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
        
        # Screen positions in clockwise order starting from Bottom-Center
        screen_positions = [
            "Bottom-Center",  # Hero's seat
            "Bottom-Left",    # 1 seat clockwise from hero
            "Top-Left",       # 2 seats clockwise
            "Top-Center",     # 3 seats clockwise
            "Top-Right",      # 4 seats clockwise
            "Bottom-Right"    # 5 seats clockwise
        ]
        
        # Find hero's index
        hero_idx = positions.index(hero_position)
        
        # Build mapping
        mapping_lines = []
        for i, screen_pos in enumerate(screen_positions):
            # Calculate actual position index (hero + i) mod 6
            pos_idx = (hero_idx + i) % 6
            actual_position = positions[pos_idx]
            
            if i == 0:
                mapping_lines.append(f"- {screen_pos}: {actual_position} (HERO - YOU)")
            else:
                mapping_lines.append(f"- {screen_pos}: {actual_position}")
        
        return "\n".join(mapping_lines)
    
    def analyze_poker_table(self, image_data: bytes, hero_position: str = "BTN") -> Dict[str, Any]:
        """
        Analyze poker table image using Gemini
        
        Args:
            image_data: Raw image bytes
            hero_position: Hero's position (BTN, SB, BB, UTG, MP, CO)
            
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
            logger.info(f"🤖 Sending image to Gemini for analysis... Hero position: {hero_position}")
            
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Create position-specific prompt with relative positioning
            # Generate relative position map based on hero's position
            position_map = self._get_relative_positions(hero_position)
            
            position_prompt = f"""{POKER_ANALYSIS_PROMPT}

CRITICAL POSITION INFORMATION:
Hero is seated at {hero_position} position (bottom-center of screen).

RELATIVE POSITIONS FROM HERO:
{position_map}

USE THIS MAPPING: When analyzing other players, use the screen position (Top-Center, Top-Right, etc.) to determine their poker position based on the above mapping. DO NOT try to count from the dealer button - use Hero's known position as the anchor point."""
            
            # Generate analysis
            response = self.model.generate_content([
                position_prompt,
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
        
        Returns simplified view for main UI with 4 decision metrics
        """
        try:
            game_info = analysis.get("game_info", {})
            recommendation = analysis.get("recommendation", {})
            detailed = analysis.get("detailed_analysis", {})
            
            # Format action with raise amount if applicable
            action = recommendation.get("action", "Unknown")
            raise_amount = recommendation.get("raise_amount_dollars", "N/A")
            
            # If action is Raise and we have an amount, combine them
            if action == "Raise" and raise_amount != "N/A":
                action_display = f"Raise {raise_amount}"
            else:
                action_display = action
            
            return {
                "success": True,
                "hero_turn": game_info.get("is_hero_turn", False),
                
                # Main display - 4 decision metrics
                "recommendation": {
                    "action": action_display,
                    "pot_odds": recommendation.get("pot_odds", "N/A"),
                    "equity_vs_range": recommendation.get("equity_vs_range", "N/A"),
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
