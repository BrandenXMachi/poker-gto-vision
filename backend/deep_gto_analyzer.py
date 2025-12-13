"""
Deep Mode Player Tracker using Gemini Flash
Only identifies player names and their current actions - no GTO analysis
"""

import os
import json
import logging
from typing import Dict, Any
import google.generativeai as genai
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API key configured for Deep Mode")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set")


PLAYER_TRACKING_PROMPT = """Analyze this poker table image and identify each player's NAME and BETTING ACTION.

## Your Task:
For EACH visible player, identify:
1. **Player NAME** (text label near player)
2. **Betting ACTION** with exact dollar amounts

## How to Find Bet Amounts:
- Look for CHIPS or CHIP STACKS in front of each player
- Look for TEXT showing dollar amounts near the chips (e.g., "$35", "$100")
- Check the area between the player and the center pot
- Bet amounts may appear as overlays or text labels near chip graphics
- If chips are visible but no text, estimate based on chip appearance

## Action Types:
- "Raised $XX" - if there are chips in front of them with an amount
- "3bet to $XX" - if they re-raised
- "Called $XX" - if they matched a bet
- "Folded" - if no cards visible or marked as folded
- "Checked" - if no bet but still in hand
- "All-in $XX" - if all their chips are in
- "Hero's turn" - bottom-center player when buttons are visible
- "Bet $XX" - first to bet on this street
- "No action yet" - waiting to act

## Critical:
- ALWAYS include dollar amounts when you see chips
- Look carefully at the betting area in front of each player
- Chip stacks = money on the table = bet amount
- Even if text is small, try to read the amounts

Output ONLY valid JSON:
{
  "success": true,
  "players": [
    {"name": "PlayerName", "action": "Raised $35"},
    {"name": "AnotherPlayer", "action": "Folded"}
  ]
}

Remember: The bet amounts are CRITICAL - look hard for those dollar values!"""


class DeepGTOAnalyzer:
    """
    Deep Mode using Gemini Flash for player tracking
    Only extracts player names and actions - no strategy analysis
    """
    
    def __init__(self):
        """Initialize Gemini Flash for player tracking"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Deep Mode initialized (Gemini Flash - Player Tracking)")
    
    def analyze(self, image_data: bytes, hero_position: str = None, blinds: str = None) -> Dict[str, Any]:
        """
        Track players and their actions using Gemini Flash
        
        Args:
            image_data: Raw image bytes
            hero_position: Ignored
            blinds: Ignored
            
        Returns:
            Dictionary with player names and actions
        """
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }
        
        try:
            logger.info("🔍 Deep Mode tracking players with Gemini Flash...")
            
            # Load image
            image = Image.open(BytesIO(image_data))
            
            # Call Gemini
            response = self.model.generate_content([PLAYER_TRACKING_PROMPT, image])
            result_text = response.text.strip()
            
            # Clean up JSON
            if "```json" in result_text:
                start = result_text.find("```json") + 7
                end = result_text.find("```", start)
                if end != -1:
                    result_text = result_text[start:end].strip()
            elif "```" in result_text:
                start = result_text.find("```") + 3
                end = result_text.find("```", start)
                if end != -1:
                    result_text = result_text[start:end].strip()
            
            result_text = result_text.strip()
            if not result_text.startswith("{"):
                json_start = result_text.find("{")
                if json_start != -1:
                    result_text = result_text[json_start:]
            
            if not result_text.endswith("}"):
                json_end = result_text.rfind("}")
                if json_end != -1:
                    result_text = result_text[:json_end + 1]
            
            result = json.loads(result_text)
            
            # Build player summary
            players = result.get("players", [])
            player_summary = "\n".join([f"{p['name']}: {p['action']}" for p in players])
            
            # Return in expected format
            transformed = {
                "success": result.get("success", True),
                "extracted_data": {
                    "hero_position": "unknown",
                    "hero_cards": [],
                    "board_cards": [],
                    "pot_size_dollars": "unknown",
                    "street": "unknown",
                    "is_hero_turn": True,
                    "villain_positions": {},
                    "visual_description": player_summary,
                    "players": players
                },
                "recommendation": {
                    "action": "Player Tracking Mode",
                    "reasoning": player_summary,
                    "pot_odds": {"value": "N/A", "calculation": "Player tracking only"},
                    "hand_equity": {"value": "N/A", "calculation": "Player tracking only"},
                    "implied_odds": {"value": "N/A", "calculation": "Player tracking only"},
                    "fold_equity": {"value": "N/A", "calculation": "Player tracking only"},
                    "expected_value": {"value": "N/A", "calculation": "Player tracking only"},
                    "optimal_play": player_summary
                }
            }
            
            logger.info("✅ Deep Mode player tracking complete")
            return transformed
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse response: {e}")
            if 'result_text' in locals():
                logger.error(f"Raw response: {result_text[:1000]}")
                return {
                    "success": False,
                    "error": f"Failed to parse response: {str(e)}",
                    "raw_response": result_text[:1000]
                }
            return {
                "success": False,
                "error": "No response received"
            }
            
        except Exception as e:
            logger.error(f"❌ Deep Mode error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
