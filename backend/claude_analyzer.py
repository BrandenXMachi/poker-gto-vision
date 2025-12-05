"""
Claude-powered poker table analyzer
Uses Anthropic's Claude Sonnet 3.5 for comprehensive poker analysis
"""

import os
import base64
import json
import logging
from typing import Dict, Any
from anthropic import Anthropic
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Configure Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("✅ Claude API key configured")
else:
    client = None
    logger.warning("⚠️ ANTHROPIC_API_KEY not set - add it to environment variables on Render")

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
    "action": "<Fold|Call|Raise to X BB>",
    "raise_amount_bb": <number or null>,
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
   
9. **GTO Recommendation with Raise Sizing**: 
   - Provide theoretically optimal play based on position, pot odds, and situation
   - Consider: position strength, pot odds, likely ranges, stack depths
   - **IMPORTANT: When recommending Raise:**
     * Include specific raise size in BB (big blinds)
     * Action should be "Raise to X BB" (e.g., "Raise to 6 BB")
     * Set raise_amount_bb to the specific number (e.g., 6)
     * Standard preflop raises: 2.5-3x open, 3x 3-bet
     * Standard postflop raises: 50-75% pot (smaller sizing), 100-150% pot (larger sizing)
   - **For Fold or Call:**
     * Action should be "Fold" or "Call"
     * Set raise_amount_bb to null

REMEMBER: The "D" button marker is THE KEY to determining position correctly!

Return ONLY valid JSON, no markdown, no extra text."""


class ClaudePokerAnalyzer:
    """Poker table analyzer using Claude Sonnet 3.5"""
    
    def __init__(self):
        """Initialize Claude client"""
        if not client:
            logger.warning("⚠️ Claude client not initialized - API key missing")
        else:
            logger.info("✅ Claude analyzer initialized")
    
    def analyze_poker_table(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze poker table image using Claude
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with analysis results
        """
        # Check if API key is configured
        if not ANTHROPIC_API_KEY or not client:
            logger.error("❌ ANTHROPIC_API_KEY not configured!")
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY not configured. Please add it to Render environment variables."
            }
        
        try:
            logger.info("🤖 Sending image to Claude for analysis...")
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image type
            try:
                img = Image.open(BytesIO(image_data))
                img_format = img.format.lower() if img.format else 'jpeg'
                if img_format == 'jpg':
                    img_format = 'jpeg'
            except:
                img_format = 'jpeg'
            
            # Generate analysis using Claude
            message = client.messages.create(
                model="claude-sonnet-3-5-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{img_format}",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": POKER_ANALYSIS_PROMPT
                            }
                        ],
                    }
                ],
            )
            
            # Extract response text
            analysis_text = message.content[0].text.strip()
            
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
            
            logger.info(f"✅ Claude analysis complete: {analysis['recommendation']['action']}")
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Claude response as JSON: {e}")
            raw_text = analysis_text[:1000] if 'analysis_text' in locals() else 'N/A'
            logger.error(f"Raw response: {raw_text}")
            return {
                "success": False,
                "error": f"JSON parse error: {str(e)}",
                "raw_response": raw_text
            }
            
        except Exception as e:
            logger.error(f"❌ Claude analysis error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}"
            }
    
    def format_for_frontend(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Claude analysis for frontend display
        
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
