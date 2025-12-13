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


CLAUDE_SIMPLE_PROMPT = """You are an elite poker GTO expert. Analyze this poker table screenshot and provide strategy advice.

## CRITICAL RULES:
1. ALWAYS provide a recommendation - NEVER say you cannot identify cards
2. If cards are unclear, make your best inference or provide general GTO strategy
3. Your job is to HELP the player, not to refuse analysis
4. Output ONLY valid JSON

## What to Analyze:

**Table State:**
- Pot size and street (preflop/flop/turn/river)
- Community cards (if visible)
- Number of active players (those with card backs)
- Hero position (player at bottom center)
- Stack sizes and bet amounts

**Your Recommendation:**
Provide the optimal GTO play with reasoning based on:
- Position dynamics
- Pot odds
- Stack-to-pot ratios
- Player count
- Any visible stats or betting patterns

## Required JSON Output:

{
  "success": true,
  "visual_description": "Brief description of the table state you observe",
  "optimal_action": "Fold|Call|Raise $X.XX|Bet $X.XX|Check",
  "analysis": "Explain why this is the GTO optimal play considering the visible game state, position, pot odds, and stack dynamics."
}

**Remember:** Always provide your best strategic advice. Never refuse to analyze."""


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
                    "visual_description": result.get("visual_description", "")
                },
                "recommendation": {
                    "action": result.get("optimal_action", "Unknown"),
                    "reasoning": result.get("analysis", ""),
                    "pot_odds": {"value": "N/A", "calculation": "Inferred from image"},
                    "hand_equity": {"value": "N/A", "calculation": "Inferred from image"},
                    "implied_odds": {"value": "N/A", "calculation": "Inferred from image"},
                    "fold_equity": {"value": "N/A", "calculation": "Inferred from image"},
                    "expected_value": {"value": "N/A", "calculation": "Inferred from image"},
                    "optimal_play": result.get("analysis", "")
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
