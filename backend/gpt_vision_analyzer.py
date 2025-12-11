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


SYSTEM_PROMPT = """You are an expert poker analyst with computer vision capabilities. You will analyze a poker table screenshot and provide:
1. Visual data extraction (what you see)
2. Mathematical analysis (5 metrics)
3. Optimal decision recommendation

You must output valid JSON only."""


USER_PROMPT_TEMPLATE = """Analyze this GGPoker screenshot and provide a complete poker analysis.

**HERO INFORMATION:**
- Hero position: {hero_position}
- Blinds: {blinds}
- Hero is at BOTTOM-CENTER of the table

**POSITION MAPPING:**
{position_mapping}

---

## PART 1: VISUAL DATA EXTRACTION

Extract all visible information from the poker table:

**Required Data:**
1. **Hero's Cards**: Extract rank and suit (e.g., ["A♠", "Q♠"])
2. **Board Cards**: All community cards visible (e.g., ["8♦", "6♦", "9♥"]) or [] if preflop
3. **Pot Size**: Look for "Total Pot : $X.XX" text
4. **Street**: Determine from community cards (0=preflop, 3=flop, 4=turn, 5=river)
5. **Hero's Turn**: Check if action buttons (Fold/Call/Raise) are visible at bottom

**🃏 FOLD DETECTION - CRITICAL (PRIMARY METHOD)**:

The MOST RELIABLE indicator of an active (non-folded) player:
→ VISIBLE CARD BACKS at their position

For EACH opponent position, check:
- ✅ Can you see 2 card backs (face-down cards)? → ACTIVE (has_folded: false)
- ❌ No card backs visible? → FOLDED (has_folded: true)

**Detection Rules**:
1. ONLY players with visible card backs are active
2. Ignore seat appearance, colors, brightness - focus on CARDS ONLY
3. Hero might be heads-up even with 5 occupied seats
4. This is ESSENTIAL for accurate GTO analysis

DO NOT include folded players (no card backs) in villain_positions.
Only report active players with visible cards.

6. **Villain Data**: For each ACTIVE (card backs visible) player, extract:
   - Player name
   - Position (based on screen location)
   - Stack size (in BB if visible)
   - VPIP percentage (if shown above name)
   - Current bet amount
   - Folded status (should be false for all reported players)
7. **Action to Hero**: Describe the betting action (e.g., "$2.00 to call" or "Can check")
8. **Betting History**: List visible actions in sequence

---

## PART 2: POKER DECISION ANALYSIS

Based on the extracted data, calculate the 5 key metrics:

### 1. POT ODDS
- Formula: (Amount to call) / (Pot after you call)
- Express as ratio (e.g., "3:1") or percentage (e.g., "25%")
- Show calculation steps

### 2. HAND EQUITY
- Estimate hero's winning % vs villain's range
- Consider:
  * Villain's VPIP (tight = narrow range, loose = wide range)
  * Position and action sequence
  * Board texture
- Show range estimation and equity calculation

### 3. IMPLIED ODDS
- Estimate additional money you can win on future streets
- Factors:
  * Stack depth (deeper = higher implied odds)
  * Board texture (wet = lower implied odds)
  * Drawing hands = higher implied odds
- Express as ratio or High/Medium/Low

### 4. FOLD EQUITY
- Estimate % villain folds to a bet/raise
- Factors:
  * Villain's VPIP (tight players fold more)
  * Pot size (small pots = easier folds)
  * Board texture (scary boards = more folds)
  * Bet sizing
- Express as percentage

### 5. EXPECTED VALUE (EV)
- For Call: EV = (Hand Equity × Pot) - Call Amount + Implied Odds
- For Bet/Raise: EV = (Fold Equity × Pot) + ((1 - Fold Equity) × ((Hand Equity × Final Pot) - Bet))
- Show complete calculation
- Express in dollars (e.g., "+$2.10" or "-$0.75")

### DECISION LOGIC:
- If EV(all actions) < 0 → Fold
- If Pot Odds < Hand Equity + Implied Odds → Call is profitable
- If EV(Bet/Raise) > EV(Call) → Bet/Raise
- Choose action with highest EV

---

## OUTPUT FORMAT (JSON ONLY):

{{
  "success": true,
  "extracted_data": {{
    "hero_position": "{hero_position}",
    "hero_cards": ["card1", "card2"],
    "board_cards": [] or ["card1", "card2", "card3"],
    "pot_size_dollars": "$10.50",
    "street": "preflop|flop|turn|river",
    "hero_stack": "150 BB",
    "is_hero_turn": true|false,
    "villain_positions": {{
      "BB": {{
        "player_name": "PlayerName",
        "screen_position": "Top-Center",
        "stack": "100 BB",
        "vpip": "28%" or "N/A",
        "current_bet": "$2.00",
        "has_folded": false
      }}
    }},
    "action_to_hero": "$2.00 to call",
    "betting_history": ["UTG folds", "MP raises $2", "..."],
    "blinds": "{blinds}"
  }},
  "recommendation": {{
    "action": "Fold|Call|Check|Raise|Bet",
    "raise_amount_dollars": "$4.50" or "N/A",
    "pot_odds": {{
      "value": "3:1",
      "calculation": "Detailed pot odds calculation showing your work"
    }},
    "hand_equity": {{
      "value": "45%",
      "calculation": "Detailed equity calculation vs villain range"
    }},
    "implied_odds": {{
      "value": "High",
      "calculation": "Explanation of implied odds factors"
    }},
    "fold_equity": {{
      "value": "35%",
      "calculation": "Explanation of fold equity estimation"
    }},
    "expected_value": {{
      "value": "+$2.10",
      "calculation": "Complete EV formula with all components"
    }},
    "optimal_play": "Multi-sentence explanation of why this is the best long-term decision based on the mathematics above"
  }}
}}

**CRITICAL RULES:**
1. Return ONLY valid JSON, no markdown, no extra text
2. Extract ONLY what you can see - no assumptions
3. Be precise with card suits and ranks
4. Show all mathematical work in "calculation" fields
5. Base decisions purely on mathematics and GTO principles
6. If hero's cards aren't visible, set success: false
7. If it's not hero's turn, note this in the response

Analyze the image now and provide the JSON output."""


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
            
            # Call GPT-4o with vision
            response = client.chat.completions.create(
                model="gpt-4o",
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
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
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
