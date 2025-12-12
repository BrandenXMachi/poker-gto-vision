"""
Deep GTO Analyzer using Gemini 2.0 Pro Experimental
Advanced GTO strategy with comprehensive game state analysis
Focuses on: Position, Blinds, Pot Size, Active Players, Actions, Stacks, VPIP
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


DEEP_GTO_PROMPT = """You are an elite poker GTO (Game Theory Optimal) strategist with access to comprehensive GTO databases and solver knowledge.

Your mission: Analyze this poker table and provide the mathematically optimal GTO decision based on complete game state awareness.

**HERO CONTEXT:**
- Position: {hero_position}
- Blinds: {blinds}
- Hero location: BOTTOM-CENTER of table

**POSITION MAPPING:**
{position_mapping}

---

## PHASE 1: COMPREHENSIVE GAME STATE EXTRACTION

You must extract and analyze ALL available information:

### 1. HERO INFORMATION
- **Hole Cards**: Exact rank and suit (e.g., ["A♠", "K♠"])
- **Stack Size**: In big blinds (BB)
- **Position**: {hero_position}
- **Is Action on Hero?**: Check for Fold/Call/Raise buttons at bottom

### 2. BOARD STATE
- **Community Cards**: [] if preflop, or all visible cards
- **Street**: preflop (0) | flop (3) | turn (4) | river (5)
- **Board Texture**: Analyze draws, pairs, flush/straight possibilities

### 3. POT ANALYSIS
- **Current Pot Size**: Extract from "Total Pot : $X.XX"
- **Pot in BB**: Convert using blind levels
- **SPR (Stack-to-Pot Ratio)**: Calculate for each active player

### 4. ACTIVE PLAYERS IDENTIFICATION (CRITICAL)

**PRIMARY DETECTION METHOD - CARD BACKS:**
- ✅ **ACTIVE PLAYER**: Has visible card backs (2 face-down cards) at their position
- ❌ **FOLDED PLAYER**: No card backs visible

**For each ACTIVE player (with card backs visible):**

A. **Basic Info:**
   - Player name
   - Position (BTN, SB, BB, UTG, MP, CO)
   - Screen location

B. **Stack Information:**
   - Current stack in dollars
   - Stack in BB
   - Effective stack vs hero
   - SPR (Stack-to-Pot Ratio)

C. **VPIP Statistics (if visible):**
   - Look at TOP-LEFT corner above player name
   - Extract VPIP percentage (e.g., "28%")
   - This indicates player's playing frequency (tight vs loose)

D. **Current Action:**
   - Current bet amount (if any)
   - Action taken this street (check/bet/call/raise/fold)
   - Sizing tells (small/medium/large relative to pot)

E. **Behavioral Profile:**
   - Classify based on VPIP: <20% tight, 20-30% solid, >30% loose
   - Note any betting patterns visible

**CRITICAL RULES:**
1. ONLY report players with visible card backs
2. Ignore empty seats and folded positions
3. Count total active players for range construction
4. If only one villain → heads-up situation
5. VPIP is crucial for range estimation

### 5. BETTING HISTORY
- Extract all visible actions this hand
- Note bet sizes and patterns
- Identify aggressor positions

---

## PHASE 2: GTO DECISION CALCULATION

Using your internal GTO database and solver knowledge:

### STEP 1: RANGE CONSTRUCTION

**Hero's Range:**
- Standard GTO opening range for {hero_position}
- Adjusted for player count and stack depths
- Consider blinds and table dynamics

**Villain Ranges:**
For each active player:
- Estimate range based on:
  * Position
  * VPIP% (if available)
  * Actions taken
  * Stack size
  * Bet sizing
- Tighter range for low VPIP, wider for high VPIP

### STEP 2: EQUITY CALCULATION

- **Raw Equity**: Hero's hand vs villain ranges
- **Board Texture Impact**: How does board favor hero/villain ranges?
- **Blockers**: Does hero block key parts of villain ranges?
- **Redraw Potential**: Can hand improve on later streets?

### STEP 3: EV CALCULATIONS (ALL OPTIONS)

**FOLD:**
- EV = $0 (baseline)

**CALL:**
- Pot odds required: Call / (Pot + Call)
- Current equity vs required equity
- Implied odds: Stack depth × probability of winning more
- Reverse implied odds: Risk of being dominated
- EV(call) = (Equity × Final Pot) - Call Amount + Implied Odds

**RAISE/BET:**
- Optimal sizing: Based on GTO solver recommendations
- Fold equity: Probability villains fold (based on VPIP, position, stack)
- Equity when called: Against villain's calling range
- EV(raise) = (Fold Equity × Current Pot) + ((1 - Fold Equity) × ((Equity When Called × Final Pot) - Raise Amount))

### STEP 4: GTO DECISION MATRIX

Consider:
1. **Position Advantage**: IP vs OOP equity realization
2. **Stack Leverage**: Can you use stack pressure?
3. **Range Advantage**: Who has stronger range on this board?
4. **Polarization**: Should you bet/raise polarized or merged?
5. **Player Count**: More players = tighter requirements
6. **VPIP Integration**: Adjust strategy vs loose/tight players

### STEP 5: FINAL RECOMMENDATION

Choose action with highest EV from GTO perspective:
- **Fold**: When all other options have negative EV
- **Check/Call**: When pot odds justify, but not enough fold equity to bet/raise
- **Bet/Raise**: When combination of fold equity + equity when called exceeds passive options

---

## OUTPUT FORMAT (VALID JSON ONLY):

{{
  "success": true,
  "extracted_data": {{
    "hero_position": "{hero_position}",
    "hero_cards": ["rank+suit", "rank+suit"],
    "hero_stack": "150 BB",
    "board_cards": [],
    "street": "preflop",
    "pot_size_dollars": "$X.XX",
    "pot_size_bb": "X.X BB",
    "is_hero_turn": true,
    "active_player_count": 2,
    "villain_positions": {{
      "BB": {{
        "player_name": "PlayerName",
        "position": "BB",
        "screen_position": "Top-Left",
        "stack_dollars": "$50.00",
        "stack_bb": "100 BB",
        "effective_stack": "100 BB",
        "spr": "25.0",
        "vpip": "28%",
        "vpip_category": "loose",
        "current_bet": "$2.00",
        "action": "raise $2.00",
        "has_folded": false,
        "range_estimate": "Description of estimated range"
      }}
    }},
    "action_to_hero": "$2.00 to call",
    "betting_history": ["SB folds", "BB raises $2.00"],
    "blinds": "{blinds}",
    "board_texture": "N/A (preflop)" 
  }},
  "recommendation": {{
    "action": "Fold|Call|Check|Raise $X.XX|Bet $X.XX",
    "reasoning": "Comprehensive GTO explanation of why this is optimal",
    "pot_odds": {{
      "value": "3:1 (25%)",
      "calculation": "Need to call $2 to win $8 pot = 2/(2+8) = 25%"
    }},
    "hand_equity": {{
      "value": "45%",
      "calculation": "AKs vs BB's raising range (22+, A2s+, K9s+, QTs+, ATo+, KJo+) = ~45% equity"
    }},
    "implied_odds": {{
      "value": "High (+$15 implied)",
      "calculation": "Deep stacks (150BB), strong hand, nut potential → high implied odds"
    }},
    "fold_equity": {{
      "value": "35%",
      "calculation": "vs loose 28% VPIP player, 3-bet has ~35% fold equity based on GTO frequencies"
    }},
    "expected_value": {{
      "value": "+$3.50",
      "calculation": "EV(call) = (0.45 × $10) - $2 + $15 implied = +$3.50"
    }},
    "gto_frequency": "Mixed strategy: 70% call, 30% 3-bet",
    "range_advantage": "Villain has slight range advantage on this board",
    "optimal_play": "Detailed multi-paragraph GTO analysis explaining:
    - Why this action is GTO optimal
    - How position, stacks, and VPIP affect the decision
    - What your strategy accomplishes
    - How it balances your range
    - Alternative considerations if any"
  }}
}}

**STRICT RULES:**
1. Output ONLY valid JSON - no markdown, no extra text
2. Extract ONLY what you can see - no assumptions
3. Focus on ACTIVE players with card backs visible
4. VPIP is critical - look carefully at top-left of player names
5. Use your GTO database knowledge to calculate optimal play
6. Show complete math in all calculation fields
7. Base all decisions on mathematical expectation
8. Consider live poker dynamics (position, stacks, player types)

Analyze the table now and provide your GTO recommendation in JSON format."""


class DeepGTOAnalyzer:
    """
    Deep GTO analysis using Gemini 2.0 Pro Experimental
    Comprehensive strategy with position, stacks, VPIP, and GTO solver knowledge
    """
    
    def __init__(self):
        """Initialize Gemini 2.0 Pro model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
        logger.info("✅ Deep GTO analyzer initialized (gemini-2.0-pro-exp)")
    
    def _get_position_mapping(self, hero_position: str) -> str:
        """Generate position mapping for the model"""
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
    
    def analyze(self, image_data: bytes, hero_position: str = "BTN", blinds: str = "0.02/0.05") -> Dict[str, Any]:
        """
        Deep GTO analysis of poker table
        
        Args:
            image_data: Raw image bytes
            hero_position: Hero's poker position
            blinds: Blind levels (e.g., "0.02/0.05")
            
        Returns:
            Dictionary with comprehensive extracted data and GTO recommendation
        """
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }
        
        try:
            logger.info(f"🧠 Deep GTO analyzing... Hero: {hero_position}, Blinds: {blinds}")
            
            image = Image.open(BytesIO(image_data))
            position_map = self._get_position_mapping(hero_position)
            
            prompt = DEEP_GTO_PROMPT.format(
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
            
            logger.info(f"✅ Deep GTO analysis complete")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Deep GTO response: {e}")
            logger.error(f"Raw response: {response.text[:500]}")
            return {
                "success": False,
                "error": "Failed to parse Deep GTO response",
                "raw_response": response.text[:500]
            }
            
        except Exception as e:
            logger.error(f"❌ Deep GTO analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
