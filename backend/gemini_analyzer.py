"""
Gemini-powered poker table data extractor
Uses Google's Gemini Flash 2.0 Experimental for visual recognition ONLY
Does NOT make poker decisions - that's GPT's job
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

# Data extraction prompt - NO POKER DECISIONS
DATA_EXTRACTION_PROMPT = """You are a visual data extraction expert. Your job is to extract poker table information from this GGPoker screenshot.

**IMPORTANT**: You are NOT making poker decisions. You are ONLY extracting what you see. Another AI will make the decision.

Your response MUST be valid JSON with this exact structure:

{
  "hero_position": "<BTN|SB|BB|UTG|MP|CO>",
  "hero_cards": ["<card1>", "<card2>"],
  "board_cards": ["<card1>", "<card2>", "<card3>"] or [],
  "pot_size_dollars": "<dollar amount like $10.50>",
  "street": "<preflop|flop|turn|river>",
  "hero_stack": "<in BB, like 150 BB>",
  "is_hero_turn": <true|false>,
  "villain_positions": {
    "BB": {
      "screen_position": "Top-Center",
      "stack": "100 BB",
      "vpip": "28%" or "N/A",
      "current_bet": "$2.00" or "$0",
      "has_folded": false
    }
  },
  "action_to_hero": "<description like '$2.00 to call' or 'No action - hero can check'>",
  "betting_history": ["<action1>", "<action2>", "..."]
}

EXTRACTION GUIDELINES:

**1. HERO IDENTIFICATION**:
- Hero is ALWAYS at BOTTOM-CENTER of table
- Hero's cards are visible at bottom
- Extract hero's cards with rank AND suit (e.g., "A♠", "Q♠")

**2. POSITION IDENTIFICATION**:
- You will be told hero's position (it's provided as input)
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
- Note which players have folded

**6. BETTING ACTION**:
- Extract what you SEE - who has chips in front of them
- Describe the current bet amounts
- List betting sequence if visible
- DO NOT GUESS - only report what you can see

**7. VPIP STATS**:
- Look for VPIP percentage above each player's name
- Extract if visible, otherwise "N/A"

**8. STREET IDENTIFICATION**:
- 0 community cards = "preflop"
- 3 community cards = "flop"
- 4 community cards = "turn"
- 5 community cards = "river"

**9. HERO'S TURN**:
- Check if action buttons (Fold/Call/Raise) are visible at bottom
- Check if there's a timer or highlight on hero
- true if it's hero's turn, false otherwise

**10. SCREEN POSITIONS** (for reference):
- Bottom-Center = Hero
- Bottom-Left = 1 seat clockwise from hero
- Top-Left = 2 seats clockwise
- Top-Center = 3 seats clockwise
- Top-Right = 4 seats clockwise
- Bottom-Right = 5 seats clockwise

**CRITICAL RULES**:
- Extract ONLY what you can see - no assumptions
- Be precise with card suits and ranks
- If something isn't visible, mark as "N/A" or "Unknown"
- DO NOT make poker decisions or calculate odds
- DO NOT guess betting history - only report visible info

Return ONLY valid JSON, no markdown, no extra text."""


class GeminiDataExtractor:
    """Visual data extraction using Gemini - NO poker logic"""
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini 2.0 Flash data extractor initialized")
    
    def _get_position_mapping(self, hero_position: str) -> str:
        """Generate position mapping for Gemini"""
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
    
    def extract_data(self, image_data: bytes, hero_position: str = "BTN") -> Dict[str, Any]:
        """
        Extract poker table data using Gemini vision
        
        Args:
            image_data: Raw image bytes
            hero_position: Hero's poker position (provided by user)
            
        Returns:
            Dictionary with extracted data
        """
        if not GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY not configured!")
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured."
            }
        
        try:
            logger.info(f"👁️ Gemini extracting data... Hero position: {hero_position}")
            
            image = Image.open(BytesIO(image_data))
            position_map = self._get_position_mapping(hero_position)
            
            prompt = f"""{DATA_EXTRACTION_PROMPT}

POSITION MAPPING:
Hero is at {hero_position} position (bottom-center of screen).

{position_map}

Use this mapping to identify other players' poker positions based on their screen location.

Extract all visible data from the image now."""
            
            response = self.model.generate_content([prompt, image])
            data_text = response.text.strip()
            
            # Remove markdown if present
            if data_text.startswith("```json"):
                data_text = data_text[7:]
            if data_text.startswith("```"):
                data_text = data_text[3:]
            if data_text.endswith("```"):
                data_text = data_text[:-3]
            
            data_text = data_text.strip()
            extracted_data = json.loads(data_text)
            
            logger.info(f"✅ Gemini extraction complete: {extracted_data.get('street', 'unknown')} street")
            
            return {
                "success": True,
                "extracted_data": extracted_data
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Gemini response: {e}")
            logger.error(f"Raw response: {response.text[:500]}")
            return {
                "success": False,
                "error": "Failed to parse extraction response",
                "raw_response": response.text[:500]
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini extraction error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
