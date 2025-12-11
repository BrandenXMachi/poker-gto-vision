"""
GPT-4o Vision-powered poker analyzer
Uses Gemini's detailed extraction approach + poker decision making
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


SYSTEM_PROMPT = """You are an expert poker player and visual analyst. First extract table data precisely, then make optimal poker decisions."""


# Using Gemini's detailed extraction approach + poker decision
USER_PROMPT_TEMPLATE = """Analyze this GGPoker screenshot. Extract visual data first, then provide optimal poker strategy.

**HERO CONTEXT:**
🎯 Hero Position: {hero_position}
💵 Blinds: {blinds}
📍 Hero is at BOTTOM-CENTER of screen

**POSITION MAPPING:**
{position_mapping}

---

## PART 1: VISUAL DATA EXTRACTION

Extract poker table information precisely using these guidelines:

**1. HERO IDENTIFICATION**:
- Hero is ALWAYS at BOTTOM-CENTER of table
- Hero's cards are visible at bottom
- Extract hero's cards with rank AND suit (e.g., "A♠", "Q♠")

**2. POSITION IDENTIFICATION**:
- Hero is at {hero_position} position
- Calculate other players' positions clockwise from hero
- Positions order: BTN → SB → BB → UTG → MP → CO (clockwise)

**3. BOARD CARDS**:
- Extract ALL visible community cards
- Include rank AND suit for each (e.g., ["8♦", "6♦", "9♥"])
- Empty array [] if no community cards (preflop)

**4. POT SIZE**:
- Look for "Total Pot : $X.XX" text
- Extract exact dollar amount

**5. STACKS**:
- For hero: Look at hero's stack, convert to BB
- For villains: Extract each active player's stack in BB

**🃏 FOLD DETECTION - CRITICAL (PRIMARY METHOD)**:

The MOST RELIABLE indicator of an active (non-folded) player:
→ VISIBLE CARD BACKS at their position

For EACH opponent position, check:
- ✅ Can you see 2 card backs (face-down cards)? → ACTIVE (has_folded: false)
- ❌ No card backs visible? → FOLDED (has_folded: true)

**Detection Rules**:
1. ONLY players with visible card backs are active
2. Ignore seat appearance, colors, brightness - focus on CARDS
3. Hero might be heads-up even with 5 occupied seats
4. This is ESSENTIAL for accurate GTO analysis

**6. BETTING ACTION - CRITICAL**:
- Look at chips in front of each player
- Check bet amounts displayed
- Try to reconstruct action sequence:
  * Who opened? How much?
  * Who called?
  * Who 3-bet? To how much?
  * Who folded? (no card backs = folded)
- Describe what bet/raise hero is facing RIGHT NOW
- If unclear, state: "Action history unclear from image"

**7. VPIP STATS**:
- Look for VPIP percentage above each player's name
- Extract if visible, otherwise "N/A"

**8. STREET IDENTIFICATION**:
- 0 community cards = "preflop"
- 3 community cards = "flop"
- 4 community cards = "turn"
- 5 community cards = "river"

**9. HERO'S TURN**:
- Check if action buttons (Fold/Call/Raise) are visible
- Check for timer or highlight on hero
- true if it's hero's turn, false otherwise

**10. ACTIVE PLAYERS**:
- Count ONLY players with visible card backs
- Note which positions have folded (no cards visible)

---

## PART 2: POKER DECISION

Based on the extracted data, determine optimal play considering:
- Hand strength vs range
- Position advantage
- Pot odds & implied odds
- Number of active players
- Betting action (initial raise vs 3-bet vs 4-bet)
- Stack depths
- Opponent tendencies (VPIP if available)

---

## OUTPUT FORMAT (JSON ONLY):

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
    "hero_stack": "150 BB",
    "active_players": [
      {{
        "position": "BB",
        "name": "PlayerName",
        "stack": "100 BB",
        "vpip": "28%" or "N/A",
        "current_bet": "$1.45",
        "has_folded": false
      }}
    ],
    "folded_players": ["UTG", "MP"],
    "action_observed": "UTG raised $0.25, Hero called from BTN, BB 3-bet to $1.45, UTG folded. Hero facing $1.20 to call." OR "Action unclear - pot is $ X, appears to be facing $Y bet",
    "action_to_hero": "$1.20 to call" or "No action - can check" or "Facing bet of $X"
  }},
  "recommendation": {{
    "action": "Fold" or "Call $1.20" or "Check" or "Raise to $4.50",
    "reasoning": "Based on observed action [describe what you saw], with [hand] in {hero_position} position facing [describe bet/action], the optimal play is [action] because [2-3 sentences explaining pot odds, hand strength vs range, position, and action context]."
  }}
}}

**RULES**:
- Return ONLY valid JSON
- Be precise with card notation (rank + suit)
- If hero's cards not visible → success: false
- If not hero's turn → success: false
- Extract ONLY what you can SEE
- If betting action is unclear, state it explicitly
- Base decision on ACTUAL observed action, not assumptions"""


class GPTVisionAnalyzer:
    """Complete poker analysis using GPT-4o with Gemini's extraction approach"""
    
    def __init__(self):
        """Initialize GPT-4o vision model"""
        if not client:
            raise ValueError("OpenAI API key not configured")
        logger.info("✅ GPT-4o Vision analyzer initialized (Gemini-style prompting)")
    
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
            
            # Format user prompt (using Gemini's detailed extraction approach)
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
                max_tokens=1500,
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
