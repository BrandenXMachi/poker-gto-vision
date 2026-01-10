"""
Deep Flop Analyzer - Gemini 3.0 Flash
Two-stage analysis: Visual extraction → Strategic reasoning
Flop-only mode with comprehensive GTO analysis
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

# Stage 2: Strategic analysis prompt
STRATEGIC_ANALYSIS_PROMPT = """You are a professional poker GTO strategist. Analyze this flop situation and provide optimal strategy.

**GAME INFORMATION:**
- Blinds: {blinds}
- Hero Position: {hero_position}
- Villain Position: {villain_position}
- Preflop Pot Type: {preflop_pot_type}

**EXTRACTED DATA:**
- Hero's Cards: {hero_cards}
- Board Cards: {board_cards}
- Current Pot Size: {pot_size}
- Villain's Raise: {villain_raise}

**YOUR ANALYSIS TASK:**

1. **Hand Strength Analysis**
   - Describe hero's hand (e.g., "Top pair, top kicker and a nut flush draw")
   - Consider both made hands and draws

2. **Pot Odds Calculation**
   - If villain raised: Calculate pot odds as percentage
   - Formula: (Call amount) / (Pot after call) × 100
   - Example: To call $0.50 into pot of $1.25 = $0.50 / ($1.25 + $0.50) = 28.6%

3. **Equity Estimation**
   - Estimate hero's equity vs villain's likely range
   - Consider villain's position and preflop pot type
   - Provide percentage or range (e.g., "65%" or "≈65%-68%")

4. **Expected Value (EV)**
   - Calculate EV for calling (if facing a raise)
   - Formula: (Equity × Pot) - Call amount
   - Express in dollars (e.g., "+$0.85" or "-$0.22")

5. **Optimal Strategy**
   - Recommend ONE action (or two if equally optimal):
     * FOLD
     * CHECK
     * CALL
     * RAISE [X]% of pot (e.g., "RAISE 75% of pot")
     * CHECK-RAISE [X]% of pot
     * CHECK-CALL max: $[X]
   - Explain WHY this is optimal

**OUTPUT FORMAT (JSON ONLY):**
{
  "game_summary": "$0.02/$0.05 (6 player holdem game)",
  "hero_summary": "in position with Ace of spades and King of spades",
  "board_summary": "3 of spades, 7 of spades and K of diamonds",
  "phase": "Flop",
  "villain_summary": "Under the Gun and has raised $0.5" or "Under the Gun - no raise",
  "hand_strength": "Top pair, top kicker and a nut flush draw",
  "pot_odds": "24.4%" or "N/A",
  "equity": "≈65%-68%" or "66%",
  "ev_call": "+$0.85" or "N/A",
  "optimal_strategy": "RAISE 100% of pot",
  "reasoning": "Detailed explanation of why this strategy is optimal based on hand strength, position, pot odds, equity, and EV"
}

**IMPORTANT RULES:**
- Use exact card names from input (e.g., "Ace of spades" not "A♠")
- Calculate pot odds ONLY if villain raised
- Show your math work in reasoning
- Be precise with percentages and dollar amounts
- If no clear optimal play, provide both options

Return ONLY valid JSON, no markdown, no extra text."""


class DeepFlopAnalyzer:
    """Deep flop analysis using Gemini 3.0 Flash - Two-stage processing"""
    
    def __init__(self):
        """Initialize Gemini 3.0 Flash model"""
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
        logger.info("✅ Deep Flop Analyzer initialized (Gemini 3.0 Flash Preview)")
    
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
            # STAGE 1: Visual Extraction
            logger.info("👁️ Stage 1: Visual extraction with Gemini 3.0 Flash")
            
            image = Image.open(BytesIO(image_data))
            
            response_stage1 = self.model.generate_content([VISUAL_EXTRACTION_PROMPT, image])
            extraction_text = response_stage1.text.strip()
            
            # Remove markdown if present - be more aggressive
            if "```json" in extraction_text:
                extraction_text = extraction_text.split("```json")[1].split("```")[0]
            elif "```" in extraction_text:
                extraction_text = extraction_text.split("```")[1].split("```")[0]
            
            # Clean up the text - remove literal \n strings and extra whitespace
            extraction_text = extraction_text.replace("\\n", " ").strip()
            # Remove any leading newlines or whitespace
            while extraction_text and extraction_text[0] in ['\n', '\r', ' ', '\t']:
                extraction_text = extraction_text[1:]
            
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
            
            # STAGE 2: Strategic Analysis
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
            
            response_stage2 = self.model.generate_content(analysis_prompt)
            analysis_text = response_stage2.text.strip()
            
            # Remove markdown if present - be more aggressive
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0]
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0]
            
            # Clean up the text - remove literal \n strings and extra whitespace
            analysis_text = analysis_text.replace("\\n", " ").strip()
            # Remove any leading newlines or whitespace
            while analysis_text and analysis_text[0] in ['\n', '\r', ' ', '\t']:
                analysis_text = analysis_text[1:]
            
            analysis = json.loads(analysis_text)
            
            logger.info(f"✅ Stage 2 complete: {analysis.get('optimal_strategy', 'Unknown')}")
            
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
                    "villain_position": villain_position
                },
                "recommendation": {
                    "action": analysis.get("optimal_strategy", "Unknown"),
                    "reasoning": self._format_analysis_display(analysis, blinds)
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
    
    def _format_analysis_display(self, analysis: Dict[str, Any], blinds: str) -> str:
        """Format the analysis into the specified display format"""
        lines = []
        
        # Game summary
        lines.append(f"{analysis.get('game_summary', 'Unknown game')}")
        lines.append(f"Hero: {analysis.get('hero_summary', 'Unknown position')}")
        lines.append(f"Board: {analysis.get('board_summary', 'Unknown board')}")
        lines.append(f"Phase: {analysis.get('phase', 'Flop')}")
        lines.append(f"Villain: {analysis.get('villain_summary', 'Unknown villain')}")
        lines.append("")
        
        # Hand strength
        lines.append(f"Hand strength: {analysis.get('hand_strength', 'Unknown')}")
        
        # Metrics
        if analysis.get('pot_odds') and analysis.get('pot_odds') != "N/A":
            lines.append(f"Pot odds: {analysis.get('pot_odds')}")
        
        if analysis.get('equity'):
            lines.append(f"Equity: {analysis.get('equity')}")
        
        if analysis.get('ev_call') and analysis.get('ev_call') != "N/A":
            lines.append(f"EV(call): {analysis.get('ev_call')}")
        
        lines.append("")
        
        # Optimal strategy
        lines.append(f"Optimal strategy: {analysis.get('optimal_strategy', 'Unknown')}")
        
        # Reasoning
        if analysis.get('reasoning'):
            lines.append("")
            lines.append("Analysis:")
            lines.append(analysis.get('reasoning'))
        
        return "\n".join(lines)
