"""
GPT-4o Vision-powered poker analyzer
Single API call for both visual extraction AND poker decision
"""

import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("✅ OpenAI GPT-4o Vision configured")
else:
    logger.warning("⚠️ OPENAI_API_KEY not set")
    client = None


SYSTEM_PROMPT = """You are an expert poker player and analyst. Analyze poker table screenshots and provide clear, optimal decisions."""


USER_PROMPT_TEMPLATE = """Analyze this GGPoker poker table screenshot and determine the optimal play.

**CRITICAL CONTEXT - READ CAREFULLY:**
🎯 HERO'S ACTUAL POSITION: {hero_position}
💵 BLINDS: {blinds}
📍 Hero is physically at BOTTOM-CENTER of screen

**IMPORTANT - Position Mapping (Hero's actual seat context):**
{position_mapping}

**What to analyze:**
- Hero's cards (visible at bottom of screen)
- Community cards on the board
- Pot size and current bet
- Active opponents (look for card backs at their positions)
- Betting action facing hero

**Your task:**
Determine the most optimal play (Fold, Call, Check, Raise, or Bet) and explain WHY this is the best decision.

**REMEMBER TO CONSIDER:**
- Hero is in {hero_position} position (NOT Button unless specified as BTN)
- Hand strength relative to position
- Position advantage in {hero_position}
- Pot odds and implied odds at {blinds} stakes
- Opponent tendencies (if VPIP visible)
- Board texture
- Stack sizes

**Output Format (JSON only):**
{{
  "success": true,
  "extracted_data": {{
    "hero_position": "{hero_position}",
    "hero_cards": ["A♠", "Q♠"],
    "board_cards": ["8♦", "6♦", "9♥"] or [],
    "pot_size_dollars": "$10.50",
    "street": "preflop|flop|turn|river",
    "is_hero_turn": true,
    "blinds": "{blinds}"
  }},
  "recommendation": {{
    "action": "Fold" or "Call" or "Check" or "Raise $4.50" or "Bet $3.00",
    "reasoning": "Detailed 2-3 sentence explanation of why this is the mathematically optimal play based on hand strength, position, pot odds, and opponent tendencies."
  }}
}}

**Rules:**
- Return ONLY valid JSON
- Be precise with card notation (rank + suit)
- If hero's cards not visible → success: false
- If not hero's turn → success: false
- Keep reasoning clear and concise"""


class GPTVisionAnalyzer:
    """Complete poker analysis using GPT-4o with vision"""
    
    def __init__(self):
        """Initialize GPT-4o vision model"""
        if not client:
            raise ValueError("OpenAI API key not configured")
        logger.info("✅ GPT-4o Vision analyzer initialized")
    
    def _get_position_mapping(self, hero_position: str) -> str:
        """Generate position mapping string"""
        positions = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
        screen_positions = [
            "Bottom-Center", "Bottom-Left", "Top-Left",
            "Top-Center", "Top-Right", "Bottom-Right"
        ]
        
        hero_idx = positions.index(hero_position)
        mapping = []
        for i, screen_pos in enumerate(screen_positions):
            pos_idx = (hero_idx + i) % 6
            poker_pos = positions[pos_idx]
            if i == 0:
                mapping.append(f"- {screen_pos}: {poker_pos} (HERO)")
            else:
                mapping.append(f"- {screen_pos}: {poker_pos}")
        
        return "\n".join(mapping)
    
    def _encode_image(self, image_data: bytes) -> str:
        """Encode image to base64"""
        return base64.b64encode(image_data).decode('utf-8')
    
    def analyze(self, image_data: bytes, hero_position: str = "BTN", blinds: str = "0.02/0.05") -> Dict[str, Any]:
        """
        Complete analysis using GPT-4o vision
        
        Args:
            image_data: Raw image bytes
            hero_position: Hero's poker position
            blinds: Blind levels
            
        Returns:
            Dictionary with extracted data and recommendation
        """
        try:
            logger.info(f"👁️ GPT-4o analyzing... Hero: {hero_position}, Blinds: {blinds}")
            
            # Encode image
            base64_image = self._encode_image(image_data)
            position_map = self._get_position_mapping(hero_position)
            
            # Format user prompt
            user_prompt = USER_PROMPT_TEMPLATE.format(
                hero_position=hero_position,
                blinds=blinds,
                position_mapping=position_map
            )
            
            # Call GPT-4o with vision (latest stable version)
            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            if content is None:
                logger.error("❌ GPT-4o returned empty response")
                return {
                    "success": False,
                    "error": "GPT returned empty response - try again"
                }
            
            result_text = content.strip()
            result = json.loads(result_text)
            
            logger.info(f"✅ GPT-4o analysis complete")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse GPT-4o response: {e}")
            return {
                "success": False,
                "error": "Failed to parse GPT response"
            }
            
        except Exception as e:
            logger.error(f"❌ GPT-4o analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
