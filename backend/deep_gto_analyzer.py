"""
Deep GTO Analyzer using Claude 3.5 Sonnet v2
Simplified visual analysis - Claude describes the table and recommends optimal play
No position/blinds input needed - Claude infers everything from the image
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
    logger.info("✅ Anthropic API key configured")
else:
    anthropic_client = None
    logger.warning("⚠️ ANTHROPIC_API_KEY not set")


CLAUDE_SIMPLE_PROMPT = """Analyze this poker table screenshot and identify each player's NAME and current ACTION.

## Your Task:
Look at the poker table and for EACH PLAYER visible, extract:
1. Player NAME (text near their seat)
2. Their current ACTION/STATE

## Player Actions to Identify:
- "Raised $XX" - if they made a raise
- "Folded" - if they folded
- "Called $XX" - if they called
- "Checked" - if they checked
- "All-in $XX" - if they're all-in
- "Hero's turn" - if it's the bottom-center player's turn to act
- "No action yet" - if they haven't acted
- "Waiting" - if seat is waiting/empty

## Hero Identification:
The HERO is always the player at the BOTTOM-CENTER of the screen.

## Required JSON Output:

{
  "success": true,
  "players": [
    {"name": "Brain", "action": "Raised $35"},
    {"name": "Chad", "action": "Folded"},
    {"name": "Tim", "action": "Folded"},
    {"name": "Mike", "action": "3bet to $100"},
    {"name": "Branden", "action": "Hero's turn"},
    {"name": "Samantha", "action": "No action yet"}
  ]
}

**Important:**
- Output ONLY valid JSON
- List ALL visible players
- Extract exact player names from the image
- Be specific about bet amounts when visible"""


class DeepGTOAnalyzer:
    """
    Deep GTO analysis using Claude 3.5 Sonnet v2 (20241022)
    Simplified approach - Claude infers everything from image alone
    """
    
    def __init__(self):
        """Initialize Claude 3.5 Sonnet"""
        self.client = anthropic_client
        logger.info("✅ Deep GTO analyzer initialized (Claude 3.5 Sonnet v2)")
    
    def analyze(self, image_data: bytes, hero_position: str = None, blinds: str = None) -> Dict[str, Any]:
        """
        Deep GTO analysis using Claude 3.5 Sonnet
        
        Args:
            image_data: Raw image bytes
            hero_position: Ignored - Claude infers from image
            blinds: Ignored - Claude infers from image
            
        Returns:
            Dictionary with visual description and optimal play recommendation
        """
        if not ANTHROPIC_API_KEY:
            logger.error("❌ ANTHROPIC_API_KEY not configured!")
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY not configured."
            }
        
        try:
            logger.info(f"🧠 Deep GTO analyzing with Claude 3.5 Sonnet v2...")
            
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
                                "text": CLAUDE_SIMPLE_PROMPT
                            }
                        ]
                    }
                ]
            )
            
            result_text = response.content[0].text.strip()
            
            # Clean up response - remove markdown if present
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
            
            # Find JSON object boundaries
            result_text = result_text.strip()
            if not result_text.startswith("{"):
                json_start = result_text.find("{")
                if json_start != -1:
                    result_text = result_text[json_start:]
            
            if not result_text.endswith("}"):
                json_end = result_text.rfind("}")
                if json_end != -1:
                    result_text = result_text[:json_end + 1]
            
            # Remove control characters that break JSON parsing
            import re
            result_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', result_text)
            
            result = json.loads(result_text)
            
            # Build player summary from Claude's response
            players = result.get("players", [])
            player_summary = "\n".join([f"{p['name']}: {p['action']}" for p in players])
            
            # Transform to expected format
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
                    "action": "See player actions below",
                    "reasoning": player_summary,
                    "pot_odds": {"value": "N/A", "calculation": "Player tracking mode"},
                    "hand_equity": {"value": "N/A", "calculation": "Player tracking mode"},
                    "implied_odds": {"value": "N/A", "calculation": "Player tracking mode"},
                    "fold_equity": {"value": "N/A", "calculation": "Player tracking mode"},
                    "expected_value": {"value": "N/A", "calculation": "Player tracking mode"},
                    "optimal_play": player_summary
                }
            }
            
            logger.info(f"✅ Deep GTO analysis complete (Claude 3.5 Sonnet)")
            
            return transformed
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Claude response: {e}")
            if 'result_text' in locals():
                logger.error(f"Raw response (first 1000 chars): {result_text[:1000]}")
                return {
                    "success": False,
                    "error": f"Failed to parse Claude response as JSON: {str(e)}",
                    "raw_response": result_text[:1000]
                }
            else:
                return {
                    "success": False,
                    "error": "Claude returned no response"
                }
            
        except Exception as e:
            logger.error(f"❌ Deep GTO analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
