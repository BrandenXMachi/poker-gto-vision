"""
Deep Flop Analyzer - Gemini 3.0 Flash
Two-stage analysis: Visual extraction → Strategic reasoning
Flop-only mode with comprehensive GTO analysis
"""

import os
import json
import logging
import re
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

# Stage 1: Simple visual extraction prompt
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

# Stage 2: Strategic analysis prompt - Simplified for Gemini 3.0
STRATEGIC_ANALYSIS_PROMPT = """You are a professional poker GTO strategist. Given the following information, analyze the flop situation:

**SITUATION:**
- Blinds: {blinds}
- Hero Position: {hero_position} 
- Villain Position: {villain_position}
- Preflop: {preflop_pot_type}
- Hero's Cards: {hero_cards}
- Board: {board_cards}
- Pot Size: {pot_size}
- Villain's Raise: {villain_raise}

**PROVIDE:**
1. **Board Connection**: How do hero's cards connect with the board? (e.g., "Top pair with King, Queen kicker" or "Flush draw and overcards")
2. **Optimal Play**: The single best action (FOLD, CHECK, CALL, RAISE X% pot, CHECK-RAISE X% pot)

**OUTPUT (JSON ONLY):**
{{
  "board_connection": "Description of how hero's hand connects with the board",
  "optimal_play": "The recommended action"
}}

Return ONLY valid JSON."""


class DeepFlopAnalyzer:
    """Deep flop analysis - Hybrid approach: Gemini 2.0 vision + Gemini 3.0 reasoning"""
    
    def __init__(self):
        """Initialize both Gemini models"""
        # Gemini 2.0 Flash for vision (proven to work)
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Gemini 3.0 Flash for strategic reasoning
        self.strategy_model = genai.GenerativeModel('gemini-3-flash-preview')
        
        logger.info("✅ Deep Flop Analyzer initialized (Gemini 2.0 vision + Gemini 3.0 strategy)")
    
    def analyze(
        self,
        image_data: bytes,
        hero_position: str = "IP",
        villain_position: str = "BTN",
        preflop_pot_type: str = "open_raise",
        blinds: str = "0.02/0.05"
    ) -> Dict[str, Any]:
        """
        Analyze flop situation using two-stage Gemini 3.0 Flash processing
        
        Stage 1: Visual extraction (cards, pot, raise)
        Stage 2: Strategic analysis (equity, EV, optimal play)
        
        Args:
            image_data: Raw image bytes
            hero_position: "IP" or "OOP"
            villain_position: "UTG", "MP", "CO", "BTN", "SB", "BB"
            preflop_pot_type: "open_raise", "3bet", "4bet"
            blinds: Blind levels (e.g., "0.02/0.05")
            
        Returns:
            Dictionary with complete analysis
        """
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }
        
        try:
            # STAGE 1: Visual Extraction with Gemini 2.0 Flash (proven)
            logger.info("👁️ Stage 1: Visual extraction with Gemini 2.0 Flash")
            
            image = Image.open(BytesIO(image_data))
            
            response_stage1 = self.vision_model.generate_content([VISUAL_EXTRACTION_PROMPT, image])
            raw_text = response_stage1.text
            
            # Find JSON by locating first { and last }
            first_brace = raw_text.find('{')
            last_brace = raw_text.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                extraction_text = raw_text[first_brace:last_brace+1]
            else:
                extraction_text = raw_text.strip()
            
            logger.info(f"Extracted text for parsing: {extraction_text[:200]}...")
            extracted_data = json.loads(extraction_text)
            
            logger.info(f"✅ Stage 1 complete: {extracted_data}")
            
            # Validate extracted data
            hero_cards = extracted_data.get("hero_cards", [])
            board_cards = extracted_data.get("board_cards", [])
            
            if len(hero_cards) != 2 or len(board_cards) != 3:
                return {
                    "success": False,
                    "error": f"Invalid card extraction: {len(hero_cards)} hero cards, {len(board_cards)} board cards"
                }
            
            # STAGE 2: Strategic Analysis with Gemini 3.0 Flash
            logger.info("🧠 Stage 2: Strategic analysis with Gemini 3.0 Flash")
            
            # Format preflop pot type for display
            pot_type_display = {
                "open_raise": "Single Raised Pot",
                "3bet": "3-Bet Pot",
                "4bet": "4-Bet Pot"
            }.get(preflop_pot_type, preflop_pot_type)
            
            analysis_prompt = STRATEGIC_ANALYSIS_PROMPT.format(
                blinds=blinds,
                hero_position="In Position" if hero_position == "IP" else "Out of Position",
                villain_position=villain_position,
                preflop_pot_type=pot_type_display,
                hero_cards=", ".join(hero_cards),
                board_cards=", ".join(board_cards),
                pot_size=extracted_data.get("pot_size", "Unknown"),
                villain_raise=extracted_data.get("villain_raise_amount", "0")
            )
            
            response_stage2 = self.strategy_model.generate_content(analysis_prompt)
            raw_text = response_stage2.text
            
            # Find JSON by locating first { and last }
            first_brace = raw_text.find('{')
            last_brace = raw_text.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                analysis_text = raw_text[first_brace:last_brace+1]
            else:
                analysis_text = raw_text.strip()
            
            logger.info(f"Extracted analysis for parsing: {analysis_text[:200]}...")
            analysis = json.loads(analysis_text)
            
            logger.info(f"✅ Stage 2 complete: {analysis.get('optimal_play', 'Unknown')}")
            
            # Format final response
            return {
                "success": True,
                "extracted_data": {
                    "hero_cards": hero_cards,
                    "board_cards": board_cards,
                    "pot_size_dollars": extracted_data.get("pot_size", "Unknown"),
                    "villain_raise": extracted_data.get("villain_raise_amount", "0"),
                    "street": "flop",
                    "hero_position": hero_position,
                    "villain_position": villain_position,
                    "board_description": analysis.get("board_connection", "Unknown"),
                    "hand_description": f"{', '.join(hero_cards)}"
                },
                "recommendation": {
                    "action": analysis.get("optimal_play", "Unknown"),
                    "reasoning": analysis.get("board_connection", "")
                },
                "analysis": analysis
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Gemini response: {e}")
            logger.error(f"Raw response text: {response_stage2.text if 'response_stage2' in locals() else response_stage1.text}")
            return {
                "success": False,
                "error": f"Failed to parse analysis response: {str(e)}"
            }
            
        except Exception as e:
            logger.error(f"❌ Deep flop analysis error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
