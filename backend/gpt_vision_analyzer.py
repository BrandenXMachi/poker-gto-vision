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

**What to analyze - BE DETAILED:**
1. **Hero's cards** (visible at bottom of screen)
2. **Community cards** on the board (if any)
3. **Pot size** - current total pot
4. **Action History** - CRITICAL:
   - Who opened/raised? How much?
   - Who called?
   - Who folded? (look for grayed out players or missing cards)
   - Is this a 3-bet? 4-bet? Squeeze?
   - What action is Hero facing RIGHT NOW?
5. **Active players** - Which players still have cards?
6. **Stack sizes** visible on screen

**IF YOU CANNOT SEE CLEAR ACTION HISTORY:**
- State: "Action history unclear from image"
- Make best guess based on pot size and visible information
- Note any assumptions you're making

**Your task:**
1. Describe the betting action that has occurred
2. Identify current bet Hero must call (if any)
3. Determine optimal play considering the ACTUAL action
4. Explain reasoning based on what you observed

**REMEMBER TO CONSIDER:**
- Hero is in {hero_position} position (NOT Button unless specified as BTN)
- ACTUAL betting action (not assumed initial action)
- Whether this is a 3-bet, cold call, squeeze, etc.
- Hand strength relative to position AND action
- Position advantage in {hero_position}
- Pot odds based on ACTUAL bet to call
- Implied odds at {blinds} stakes
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
    "blinds": "{blinds}",
    "action_observed": "UTG raised to $0.25, Hero called from BTN, BB 3-bet to $1.45, UTG folded. Hero facing $1.20 more to call." OR "Action history unclear - assuming facing initial raise of $0.25"
  }},
  "recommendation": {{
    "action": "Fold" or "Call $1.20" or "Check" or "Raise to $4.50" or "Bet $3.00",
    "reasoning": "Based on the action observed: [describe action]. This hand should [Fold/Call/Raise] because [2-3 sentence explanation including pot odds, position, and action context]."
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
