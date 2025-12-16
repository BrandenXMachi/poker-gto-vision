"""
Gemini-only poker analyzer
Single API call for both visual extraction AND poker decision
Optimized for speed - perfect for quick preflop decisions
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
    logger.info("✅ Gemini API key configured")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set")


GEMINI_COMPLETE_PROMPT = """You are a poker expert with both visual analysis AND strategic decision-making capabilities.

Your task: Analyze this GGPoker screenshot and provide a complete analysis in ONE response.

**HERO INFORMATION:**
- Hero position: {hero_position}
- Blinds: {blinds}
- Hero is at BOTTOM-CENTER of the table

**⚠️ CRITICAL - POSITION MAPPING (DO NOT DEDUCE POSITIONS - USE THIS MAPPING!):**

{position_mapping}

**POSITION RULES - READ CAREFULLY:**
1. The hero position ({hero_position}) is ALWAYS CORRECT - user provided this
2. ALL other positions are derived from hero's position using the mapping above
3. DO NOT try to deduce positions from visual cues or table layout
4. ONLY use the position mapping provided above
5. Each screen position maps to exactly ONE poker position

Example: If hero is BTN (Bottom-Center):
- Bottom-Left = SB (immediately left of hero)
- Top-Left = BB (left of SB)
- Top-Center = UTG
- Top-Right = MP
- Bottom-Right = CO

**When reporting villain positions, use ONLY the poker positions from the mapping, NOT screen positions.**

---

## CRITICAL - Card Identification Instructions:

### How to Identify Cards ACCURATELY:
1. **Ranks**: A (Ace), K (King), Q (Queen), J (Jack), 10, 9, 8, 7, 6, 5, 4, 3, 2
2. **Suits**: Look at the symbol carefully:
   - ♠ = Spades (black, upside-down heart shape)
   - ♥ = Hearts (red, heart shape)
   - ♦ = Diamonds (red, diamond shape)
   - ♣ = Clubs (black, clover/trefoil shape)
3. **Pay attention to COLOR**:
   - RED suits = Hearts, Diamonds
   - BLACK suits = Spades, Clubs
4. **Double-check each card** - don't guess!

### Card Format Examples:
- "Ace of Spades" (black Ace with ♠)
- "King of Hearts" (red King with ♥)
- "Queen of Diamonds" (red Queen with ♦)
- "Jack of Clubs" (black Jack with ♣)
- "10 of Hearts", "9 of Spades", "2 of Clubs"

---

## PART 1: VISUAL DATA EXTRACTION

Extract all visible poker information:

1. **Hero's Cards**: Rank and suit - BE PRECISE! (e.g., ["Ace of Spades", "Queen of Spades"])
2. **Board Cards**: Community cards - VERIFY EACH ONE! (e.g., ["8 of Diamonds", "6 of Diamonds", "9 of Hearts"]) or [] if preflop
3. **Pot Size**: Dollar amount from "Total Pot : $X.XX"
4. **Street**: preflop (0 cards) | flop (3 cards) | turn (4 cards) | river (5 cards)
5. **Hero's Turn**: Are action buttons (Fold/Call/Raise) visible at bottom?

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

6. **Villain Data**: For each ACTIVE (card backs visible) player:
   - Player name
   - Position (from screen location)
   - Stack (in BB)
   - VPIP% (if visible above name)
   - Current bet amount
   - Folded status (should be false for all reported players)
7. **Action to Hero**: What must hero do? (e.g., "$2.00 to call")
8. **Betting History**: Visible action sequence

---

## PART 2: POKER DECISION & MATHEMATICS

Calculate the 5 key metrics and recommend optimal action:

### 1. POT ODDS
- Formula: (Call amount) / (Pot after call)
- Express as ratio OR percentage
- Show calculation

### 2. HAND EQUITY
- Hero's win % vs villain range estimate
- Consider: VPIP stats, position, actions, board texture
- Show range logic

### 3. IMPLIED ODDS
- Future money you can win
- Factors: Stack depth, board texture, hand type
- Rate as: High/Medium/Low OR ratio

### 4. FOLD EQUITY
- % villain folds to bet/raise
- Factors: VPIP, pot size, board, bet size
- Express as %

### 5. EXPECTED VALUE
- Call EV: (Equity × Pot) - Call + Implied
- Raise EV: (Fold Equity × Pot) + ((1-Fold Equity) × ((Equity × Final Pot) - Bet))
- Show calculation
- Express in dollars

### DECISION
Choose action with highest EV:
- Fold if all EVs negative
- Call if pot odds justify
- Raise/Bet if EV(aggressive) > EV(passive)

### ⚠️ CRITICAL VALIDATION BEFORE REASONING:
**MUST verify your extracted cards match your analysis!**

Hand Type Rules:
- SUITED = Both cards same suit (e.g., K♥ 8♥)
- OFFSUIT = Different suits (e.g., K♥ 8♠)
- CONNECTOR = Adjacent ranks (e.g., 9-8, K-Q)
- SUITED CONNECTOR = Same suit AND adjacent (e.g., 9♥ 8♥)
- PAIR = Same rank (e.g., K♥ K♠)

Example Checks:
- "King of Hearts" + "8 of Spades" = K8o (King-Eight OFFSUIT) - NOT suited!
- "9 of Hearts" + "8 of Hearts" = 98s (Nine-Eight SUITED connector)
- "King of Clubs" + "Queen of Clubs" = KQs (King-Queen SUITED connector)
- "Ace of Spades" + "King of Diamonds" = AKo (Ace-King OFFSUIT)

**Before writing reasoning, double-check: Do my extracted suits match my description?**

---

## OUTPUT FORMAT (VALID JSON ONLY):

{{
  "success": true,
  "extracted_data": {{
    "hero_position": "{hero_position}",
    "hero_cards": ["card1", "card2"],
    "board_cards": [],
    "pot_size_dollars": "$X.XX",
    "street": "preflop|flop|turn|river",
    "hero_stack": "150 BB",
    "is_hero_turn": true,
    "villain_positions": {{
      "BB": {{
        "player_name": "Name",
        "screen_position": "Top-Center",
        "stack": "100 BB",
        "vpip": "28%",
        "current_bet": "$2.00",
        "has_folded": false
      }}
    }},
    "action_to_hero": "$2.00 to call",
    "betting_history": ["action1", "action2"],
    "blinds": "{blinds}"
  }},
  "recommendation": {{
    "action": "Fold|Call|Check|Raise|Bet",
    "raise_amount_dollars": "$4.50",
    "pot_odds": {{
      "value": "3:1",
      "calculation": "Pot odds calculation details"
    }},
    "hand_equity": {{
      "value": "45%",
      "calculation": "Equity vs range calculation"
    }},
    "implied_odds": {{
      "value": "High",
      "calculation": "Implied odds reasoning"
    }},
    "fold_equity": {{
      "value": "35%",
      "calculation": "Fold equity estimation"
    }},
    "expected_value": {{
      "value": "+$2.10",
      "calculation": "Complete EV calculation"
    }},
    "optimal_play": "Detailed explanation of why this is the mathematically optimal decision"
  }}
}}

**RULES:**
1. Output ONLY valid JSON - no markdown, no extra text
2. Extract ONLY visible data - no guessing
3. Show math work in "calculation" fields
4. Base decisions on GTO mathematics
5. If hero's cards not visible → success: false
6. If not hero's turn → note in response

Analyze now and provide JSON output."""


class GeminiOnlyAnalyzer:
    """Complete poker analysis using Gemini Flash 2.0 only - optimized for speed"""
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini-only analyzer initialized (fast mode)")
    
    def _get_position_mapping(self, hero_position: str) -> str:
        """Generate position mapping for Gemini"""
        positions = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
        screen_positions = [
            "Bottom-Center", "Bottom-Left", "Top-Left",
            "Top-Center", "Top-Right", "Bottom-Right"
        ]
        
        # Convert IP/OOP to actual positions for Odds mode
        if hero_position == "IP":
            hero_position = "BTN"  # In Position defaults to Button
        elif hero_position == "OOP":
            hero_position = "BB"   # Out of Position defaults to Big Blind
        
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
    
    def analyze(self, image_data: bytes, hero_position: str = "BTN", blinds: str = "0.02/0.05") -> Dict[str, Any]:
        """
        Complete analysis using Gemini only
        
        Args:
            image_data: Raw image bytes
            hero_position: Hero's poker position
            blinds: Blind levels
            
        Returns:
            Dictionary with extracted data and recommendation
        """
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }
        
        try:
            logger.info(f"⚡ Gemini fast analyzing... Hero: {hero_position}, Blinds: {blinds}")
            
            image = Image.open(BytesIO(image_data))
            position_map = self._get_position_mapping(hero_position)
            
            prompt = GEMINI_COMPLETE_PROMPT.format(
                hero_position=hero_position,
                blinds=blinds,
                position_mapping=position_map
            )
            
            response = self.model.generate_content([prompt, image])
            result_text = response.text.strip()
            
            # Remove markdown if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            result = json.loads(result_text)
            
            logger.info(f"✅ Gemini complete analysis done")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Gemini response: {e}")
            logger.error(f"Raw response: {response.text[:500]}")
            return {
                "success": False,
                "error": "Failed to parse Gemini response",
                "raw_response": response.text[:500]
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
