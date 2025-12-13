"""
Deep Mode Player Tracker using Claude 3 Opus
Identifies player names and betting actions with precise bet amount detection
"""

import os
import json
import logging
import base64
from typing import Dict, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Configure Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("✅ Anthropic API key configured for Deep Mode")
else:
    anthropic_client = None
    logger.warning("⚠️ ANTHROPIC_API_KEY not set")


PLAYER_TRACKING_PROMPT = """Analyze this poker table image and identify each player's NAME and BETTING ACTION with exact dollar amounts.

## Your Task:
For EACH visible player at the table, identify:
1. **Player NAME** (text label near their seat)
2. **Betting ACTION** with EXACT dollar amounts

## Critical - Finding Bet Amounts (NOT Stack Sizes):

**IMPORTANT - What to Look For:**
- Numbers **directly on the table** in front of each player
- These are chips/bets that have been PUSHED FORWARD onto the table
- Usually between the player's seat and the center pot
- Look for dollar amounts near chip graphics ON THE TABLE

**IGNORE These Numbers:**
- Player's STACK size (their remaining chips behind)
- The center POT total
- Any large numbers that represent total chips remaining

**How to Identify Correct Bet:**
- Find the number CLOSEST to each player's seat/bubble
- This number should be ON THE TABLE, not behind/under the player
- Bet amounts are typically smaller than stack sizes
- If multiple numbers near a player, use the one closest to their seat

## Action Types (with amounts):
- "Raised $XX" or "Bet $XX" - chips in front of player
- "Reraised to $XX" - if they re-raised (never use "3bet")
- "Called $XX" - if they matched current bet
- "All-in $XX" - all chips pushed in
- "Folded" - no cards/chips, marked as folded
- "Checked" - no bet but cards visible
- "Hero (raised $XX)" - if bottom-center player already acted and it's their turn again
- "Hero's turn" - if bottom-center player needs to act for first time
- "No action yet" - waiting to act

## Special Rule for Hero:
- If the hero (bottom-center player) has chips in front of them AND action buttons are visible, format as: "Hero (raised $XX)" or "Hero (called $XX)"
- This shows they already acted but face a reraise

## Output Format (JSON ONLY):
{
  "success": true,
  "players": [
    {"name": "PlayerName", "action": "Raised $35"},
    {"name": "AnotherPlayer", "action": "Folded"},
    {"name": "ThirdPlayer", "action": "Reraised to $100"},
    {"name": "Branden", "action": "Hero (raised $25)"}
  ]
}

## Important:
- ALWAYS try to include dollar amounts when chips are visible
- Look VERY carefully at betting areas - text may be small
- If you can't see exact amount but see chips, say "Raised (amount unclear)"
- List ALL players you can see at the table"""


class DeepGTOAnalyzer:
    """
    Deep Mode using Claude 3 Opus for player tracking
    Superior OCR and vision for precise bet amount detection
    """
    
    def __init__(self):
        """Initialize Claude 3 Opus"""
        self.client = anthropic_client
        logger.info("✅ Deep Mode initialized (Claude 3 Opus - Player Tracking)")
    
    def analyze(self, image_data: bytes, hero_position: str = None, blinds: str = None) -> Dict[str, Any]:
        """
        Track players and their betting actions using Claude 3 Opus
        
        Args:
            image_data: Raw image bytes
            hero_position: Ignored
            blinds: Ignored
            
        Returns:
            Dictionary with player names and actions
        """
        if not ANTHROPIC_API_KEY:
            logger.error("❌ ANTHROPIC_API_KEY not configured!")
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY not configured."
            }
        
        try:
            logger.info("🔍 Deep Mode tracking players with Claude 3 Opus...")
            
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Call Claude with vision
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": PLAYER_TRACKING_PROMPT
                            }
                        ]
                    }
                ]
            )
            
            result_text = response.content[0].text.strip()
            
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
            
            # Remove control characters
            import re
            result_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', result_text)
            
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
            
            logger.info("✅ Deep Mode player tracking complete (Claude Opus)")
            return transformed
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Claude response: {e}")
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
