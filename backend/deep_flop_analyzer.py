"""
Deep Flop Analyzer - Stage 1: Gemini 2.0 Flash visual extraction
                    Stage 2: FlopLogicEngine deterministic GTO decision

Replaces the hybrid Gemini 3.0 strategy stage with pure Python logic.
"""

import os
import json
import logging
from typing import Dict, Any
import google.generativeai as genai
from PIL import Image
from io import BytesIO

from flop_logic_engine import FlopLogicEngine

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API key configured for Flop Analyzer")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set")

# ─────────────────────────────────────────────────────────────────────────────
#  STAGE 1: Visual extraction prompt (unchanged — proven to work)
# ─────────────────────────────────────────────────────────────────────────────

VISUAL_EXTRACTION_PROMPT = """You are a visual data extraction expert for poker tables. Extract ONLY the following information from this GGPoker screenshot:

**YOUR TASK:**
1. **Hero's cards** (2 cards at bottom-center) - Include rank AND suit (e.g., "Ace of Spades", "King of Spades")
2. **Board cards** (3 flop cards) - Include rank AND suit for each (e.g., "3 of Spades", "7 of Spades", "King of Diamonds")
3. **Villain's raise amount** - Check if there's a bet amount hero needs to call (e.g., "$0.50"). If no raise, return "0"
4. **Current pot size** - Look for "Total Pot : $X.XX" text

**CARD IDENTIFICATION RULES:**
- Ranks: A, K, Q, J, 10, 9, 8, 7, 6, 5, 4, 3, 2
- Suits: ♠ (Spades - black), ♥ (Hearts - red), ♦ (Diamonds - red), ♣ (Clubs - black)
- Format: "Rank of Suit" (e.g., "Ace of Spades", "Queen of Hearts")

**OUTPUT FORMAT (JSON ONLY):**
{
  "hero_cards": ["card1", "card2"],
  "board_cards": ["card1", "card2", "card3"],
  "villain_raise_amount": "$0.50" or "0",
  "pot_size": "$1.25"
}

Extract ONLY what you can see. Be precise. Return ONLY valid JSON, no markdown, no extra text."""


def _parse_dollar_amount(value: str) -> float:
    """
    Safely parse a dollar string to float.
    Handles: "$1.25", "1.25", "0", "$0", "0.00"
    """
    if not value or value == "0":
        return 0.0
    try:
        return float(str(value).replace("$", "").strip())
    except (ValueError, TypeError):
        return 0.0


class DeepFlopAnalyzer:
    """
    Flop analysis:
      Stage 1 — Gemini 2.0 Flash extracts cards, pot, villain raise from image
      Stage 2 — FlopLogicEngine makes the GTO decision (pure Python, no AI)
    """

    def __init__(self):
        """Initialize Gemini vision model and logic engine."""
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash')
        self.engine = FlopLogicEngine()
        logger.info("✅ Deep Flop Analyzer initialized (Gemini 2.0 vision + FlopLogicEngine)")

    def analyze(
        self,
        image_data: bytes,
        hero_position: str = "IP",
        villain_position: str = "BTN",
        preflop_pot_type: str = "open_raise",
        blinds: str = "0.02/0.05"
    ) -> Dict[str, Any]:
        """
        Analyze a flop situation.

        Args:
            image_data:        Raw image bytes from frontend capture
            hero_position:     "IP" or "OOP"
            villain_position:  "UTG", "MP", "CO", "BTN", "SB", "BB"
            preflop_pot_type:  "open_raise", "3bet", "4bet"
            blinds:            Blind levels e.g. "0.02/0.05"

        Returns:
            Dict compatible with main.py /analyze response format
        """
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }

        # ── STAGE 1: Visual extraction ────────────────────────────────────────
        try:
            logger.info("👁️ Stage 1: Gemini 2.0 Flash visual extraction")

            image = Image.open(BytesIO(image_data))
            response = self.vision_model.generate_content([VISUAL_EXTRACTION_PROMPT, image])
            raw_text = response.text

            # Robustly find the JSON object
            first_brace = raw_text.find('{')
            last_brace  = raw_text.rfind('}')

            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                extraction_text = raw_text[first_brace:last_brace + 1]
            else:
                extraction_text = raw_text.strip()

            logger.info(f"Stage 1 raw (truncated): {extraction_text[:200]}")
            extracted = json.loads(extraction_text)

        except json.JSONDecodeError as e:
            logger.error(f"❌ Stage 1 JSON parse error: {e}")
            return {
                "success": False,
                "error": f"Could not parse Gemini extraction: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Stage 1 Gemini error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Visual extraction failed: {str(e)}"
            }

        # ── Validate extracted data ───────────────────────────────────────────
        hero_cards  = extracted.get("hero_cards",  [])
        board_cards = extracted.get("board_cards", [])

        if len(hero_cards) != 2:
            return {
                "success": False,
                "error": f"Expected 2 hero cards, got {len(hero_cards)}. Please retake the photo."
            }

        if len(board_cards) != 3:
            return {
                "success": False,
                "error": f"Expected 3 flop cards, got {len(board_cards)}. Please retake the photo."
            }

        # Parse dollar amounts — handle "0", "$0.50", etc.
        pot_size_str    = extracted.get("pot_size",            "$0")
        villain_raise_str = extracted.get("villain_raise_amount", "0")

        pot_size      = _parse_dollar_amount(pot_size_str)
        villain_raise = _parse_dollar_amount(villain_raise_str)

        # Guard against zero pot (Gemini sometimes misses it)
        if pot_size <= 0:
            # Estimate pot from blinds
            try:
                bb = float(blinds.split('/')[1])
                pot_size = bb * 7  # Rough estimate: ~7BB post-preflop action
            except Exception:
                pot_size = 0.35  # Fallback

        logger.info(
            f"✅ Stage 1 complete — Hero: {hero_cards}, Board: {board_cards}, "
            f"Pot: ${pot_size:.2f}, Raise: ${villain_raise:.2f}"
        )

        # ── STAGE 2: FlopLogicEngine ──────────────────────────────────────────
        logger.info("🧠 Stage 2: FlopLogicEngine GTO decision")

        engine_result = self.engine.analyze(
            hero_cards=hero_cards,
            board_cards=board_cards,
            pot_size=pot_size,
            villain_raise=villain_raise,
            hero_position=hero_position,
            villain_position=villain_position,
            preflop_pot_type=preflop_pot_type
        )

        if not engine_result.get("success"):
            return {
                "success": False,
                "error": engine_result.get("error", "Flop logic engine failed")
            }

        logger.info(f"✅ Stage 2 complete — Action: {engine_result['action']}")

        # ── Build response compatible with main.py ────────────────────────────
        return {
            "success": True,
            "extracted_data": {
                "hero_cards":         hero_cards,
                "board_cards":        board_cards,
                "pot_size_dollars":   pot_size_str if pot_size_str != "$0" else f"${pot_size:.2f}",
                "villain_raise":      villain_raise_str,
                "street":             "flop",
                "hero_position":      hero_position,
                "villain_position":   villain_position,
                "board_description":  engine_result.get("board_description", ""),
                "hand_description":   engine_result.get("hand_description", ""),
            },
            "recommendation": {
                "action":   engine_result["action"],
                "reasoning": engine_result["reasoning"],
            },
            # Metrics block for optional debug / badge display on frontend
            "metrics": engine_result.get("metrics", {}),
        }
