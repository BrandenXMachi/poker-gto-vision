"""
Deep Mode: Hybrid Heads-Up GTO Analyzer
Uses Gemini for visual extraction + Claude for GTO analysis
"""

import os
import json
import logging
import base64
from typing import Dict, Any
from anthropic import Anthropic
import google.generativeai as genai
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Configure APIs
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("✅ Anthropic API configured for Deep Mode")
else:
    anthropic_client = None
    logger.warning("⚠️ ANTHROPIC_API_KEY not set")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API configured for Deep Mode")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set")


def build_gemini_extraction_prompt(hero_position: str, villain_position: str, villain_action: str, blinds: str):
    """Build Gemini prompt to extract game state from image"""
    return f"""You are analyzing a HEADS-UP poker hand (only 2 players). Extract ALL visible information from this poker table image.

## Game Setup (USER PROVIDED):
- Hero is at **{hero_position}** position (closest to BOTTOM of image)
- Villain is at **{villain_position}** position  
- Blinds: **${blinds}**
- Villain has **{villain_action}**

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

## Extract These Values:

1. **POT SIZE**: Look for "Total Pot: $X" or "Pot: $X" text on the table
2. **HERO'S HOLE CARDS**: The 2 cards at the BOTTOM (hero's position) - BE PRECISE!
3. **BOARD CARDS**: Community cards in center (list all visible) - VERIFY EACH ONE!
4. **STREET**: Determine from board cards (preflop=0, flop=3, turn=4, river=5)
5. **HERO'S STACK**: Total stack at hero's position (bottom)
6. **VILLAIN'S STACK**: Total stack at villain's position ({villain_position})
7. **CALL AMOUNT**: Look at hero's buttons - "Call $X" button shows the amount

## Output Format (JSON ONLY):
{{
  "success": true,
  "pot_size": "$X.XX",
  "hero_cards": ["Ace of Clubs", "10 of Diamonds"],
  "board_cards": ["10 of Clubs", "3 of Spades", "King of Diamonds", "Queen of Spades"],
  "street": "turn",
  "hero_stack": "$X.XX",
  "villain_stack": "$X.XX", 
  "call_amount": "$X.XX"
}}

**CRITICAL**: 
- CAREFULLY identify BOTH rank AND suit for EACH card
- RED cards = Hearts or Diamonds ONLY
- BLACK cards = Spades or Clubs ONLY
- If unsure about a card, look at it again more carefully
- Format: "Rank of Suit" (e.g., "Ace of Spades", "King of Hearts")"""


def build_claude_gto_prompt(extracted_data: Dict, hero_position: str, villain_position: str, villain_action: str, blinds: str):
    """Build Claude prompt for GTO analysis with extracted data"""
    
    hero_cards_str = " and ".join(extracted_data.get("hero_cards", []))
    board_str = ", ".join(extracted_data.get("board_cards", []))
    
    return f"""You are a GTO poker expert analyzing a HEADS-UP situation.

## Complete Game State:

**Hero ({hero_position}):**
- Cards: {hero_cards_str}
- Stack: {extracted_data.get('hero_stack', 'Unknown')}

**Villain ({villain_position}):**  
- Action: {villain_action}
- Stack: {extracted_data.get('villain_stack', 'Unknown')}

**Table:**
- Pot: {extracted_data.get('pot_size', 'Unknown')}
- Street: {extracted_data.get('street', 'unknown').capitalize()}
- Board: {board_str if board_str else 'Preflop (no board yet)'}
- To Call: {extracted_data.get('call_amount', 'Unknown')}
- Blinds: ${blinds}

## Your GTO Analysis Task:

Analyze this heads-up situation using GTO principles:

1. **Pot Odds**: Calculate the price hero is getting
2. **Hand Equity**: Estimate hero's equity vs villain's range  
3. **Position**: Consider IP/OOP dynamics
4. **Villain's Range**: What does villain's {villain_action} represent from {villain_position}?
5. **SPR**: Stack-to-pot ratio implications
6. **Exploitative Considerations**: Any relevant reads

## Output JSON:
{{
  "recommendation": "Fold / Call / Raise to $X.XX",
  "reasoning": "Clear 2-3 sentence GTO explanation of why this is optimal",
  "pot_odds": "X% or X:1",
  "hand_equity": "X% vs villain's {villain_action} range",
  "gto_frequency": "Fold X%, Call Y%, Raise Z%",
  "key_factors": ["Most important factor", "Second factor", "Third factor"]
}}

Provide clear, optimal GTO strategy."""


class DeepGTOAnalyzer:
    """
    Hybrid Deep Mode: Gemini extracts visual data, Claude provides GTO analysis
    """
    
    def __init__(self):
        """Initialize Gemini and Claude"""
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.claude_client = anthropic_client
        logger.info("✅ Deep Mode initialized (Gemini + Claude Hybrid)")
    
    def analyze(self, image_data: bytes, hero_position: str, villain_position: str, 
                blinds: str, villain_action: str) -> Dict[str, Any]:
        """
        Hybrid analysis: Gemini extracts data, Claude analyzes GTO
        
        Args:
            image_data: Raw image bytes
            hero_position: Hero's position
            villain_position: Villain's position
            blinds: Blind structure
            villain_action: Villain's action
            
        Returns:
            GTO recommendation with extracted data
        """
        if not GEMINI_API_KEY or not ANTHROPIC_API_KEY:
            return {
                "success": False,
                "error": "API keys not configured"
            }
        
        try:
            logger.info(f"🔄 Hybrid Mode: {hero_position} vs {villain_position} (villain {villain_action})")
            
            # STEP 1: Gemini extracts visual data
            logger.info("👁️ Step 1: Gemini extracting visual data...")
            
            image = Image.open(BytesIO(image_data))
            extraction_prompt = build_gemini_extraction_prompt(hero_position, villain_position, villain_action, blinds)
            
            gemini_response = self.gemini_model.generate_content([extraction_prompt, image])
            extracted_text = gemini_response.text.strip()
            extracted_data = self._parse_json(extracted_text)
            
            if not extracted_data.get("success"):
                return {
                    "success": False,
                    "error": "Gemini failed to extract game state"
                }
            
            logger.info(f"✅ Gemini extracted: Pot={extracted_data.get('pot_size')}, Cards={extracted_data.get('hero_cards')}")
            
            # STEP 2: Claude analyzes with GTO
            logger.info("🧠 Step 2: Claude analyzing GTO strategy...")
            
            gto_prompt = build_claude_gto_prompt(extracted_data, hero_position, villain_position, villain_action, blinds)
            
            claude_response = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2048,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": gto_prompt
                    }
                ]
            )
            
            gto_text = claude_response.content[0].text.strip()
            gto_data = self._parse_json(gto_text)
            
            logger.info(f"✅ Claude recommends: {gto_data.get('recommendation')}")
            
            # Format response
            return {
                "success": True,
                "extracted_data": {
                    "hero_position": hero_position,
                    "villain_position": villain_position,
                    "hero_cards": extracted_data.get("hero_cards", []),
                    "board_cards": extracted_data.get("board_cards", []),
                    "pot_size_dollars": extracted_data.get("pot_size", "$0"),
                    "street": extracted_data.get("street", "unknown"),
                    "hero_stack": extracted_data.get("hero_stack", "Unknown"),
                    "villain_stack": extracted_data.get("villain_stack", "Unknown"),
                    "call_amount": extracted_data.get("call_amount", "$0"),
                    "is_hero_turn": True
                },
                "recommendation": {
                    "action": gto_data.get("recommendation", "Unknown"),
                    "reasoning": gto_data.get("reasoning", ""),
                    "pot_odds": {"value": gto_data.get("pot_odds", "N/A")},
                    "hand_equity": {"value": gto_data.get("hand_equity", "N/A")},
                    "implied_odds": {"value": "N/A"},
                    "fold_equity": {"value": "N/A"},
                    "expected_value": {"value": "N/A"},
                    "gto_frequency": gto_data.get("gto_frequency", ""),
                    "key_factors": gto_data.get("key_factors", []),
                    "optimal_play": gto_data.get("reasoning", "")
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Hybrid Mode error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_json(self, text: str) -> Dict:
        """Parse JSON from AI response"""
        try:
            # Clean up markdown code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end != -1:
                    text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                if end != -1:
                    text = text[start:end].strip()
            
            text = text.strip()
            if not text.startswith("{"):
                json_start = text.find("{")
                if json_start != -1:
                    text = text[json_start:]
            
            if not text.endswith("}"):
                json_end = text.rfind("}")
                if json_end != -1:
                    text = text[:json_end + 1]
            
            # Remove control characters
            import re
            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {"success": False}
