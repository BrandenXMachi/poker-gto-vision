"""
Deep Mode: Heads-Up GTO Analyzer using Claude 3 Opus
Assumes heads-up play with manual position inputs for precise GTO analysis
"""

import os
import json
import logging
import base64
from typing import Dict, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Configure Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("✅ Anthropic API key configured for Deep Mode")
else:
    anthropic_client = None
    logger.warning("⚠️ ANTHROPIC_API_KEY not set")


def build_extraction_prompt(hero_position: str, villain_position: str, villain_action: str, blinds: str):
    """Build prompt to extract game state from image"""
    return f"""You are analyzing a HEADS-UP poker hand (only 2 players). Extract the following information from this poker table image:

## Game Setup:
- Hero is at **{hero_position}** position (closest to BOTTOM of image)
- Villain is at **{villain_position}** position  
- Blinds: **${blinds}**
- Villain has **{villain_action}**

## Extract These Values:

1. **POT SIZE**: Look for text like "Total Pot: $X" or "Pot: $X" on the table
2. **HERO'S HOLE CARDS**: The 2 cards at the BOTTOM (hero's position)
3. **BOARD CARDS**: Community cards in center (if any)
4. **STREET**: Determine from board cards (Preflop=0 cards, Flop=3, Turn=4, River=5)
5. **HERO'S STACK**: Stack size at hero's position (bottom)
6. **VILLAIN'S STACK**: Stack size at villain's position ({villain_position})
7. **CALL AMOUNT**: Look at hero's action buttons - find the "Call $X" button amount

## Output ONLY this JSON:
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

**Critical**: 
- Pot size is the center pot total
- Call amount is from hero's buttons (the amount villain has bet)
- All amounts in dollars
- Card format: "Rank of Suit" (e.g., "Ace of Spades", "10 of Hearts")
"""


def build_gto_prompt(extracted_data: Dict, hero_position: str, villain_position: str, villain_action: str, blinds: str):
    """Build GTO analysis prompt with extracted game state"""
    
    hero_cards_str = " and ".join(extracted_data.get("hero_cards", []))
    board_str = ", ".join(extracted_data.get("board_cards", []))
    
    prompt = f"""You are a GTO poker expert. Analyze this HEADS-UP situation and provide optimal strategy.

## Game State:
- **Hero Position**: {hero_position} 
- **Hero Stack**: {extracted_data.get('hero_stack', 'Unknown')}
- **Hero Cards**: {hero_cards_str}

- **Villain Position**: {villain_position}
- **Villain Stack**: {extracted_data.get('villain_stack', 'Unknown')}  
- **Villain Action**: {villain_action}

- **Pot Size**: {extracted_data.get('pot_size', 'Unknown')}
- **Street**: {extracted_data.get('street', 'Unknown').capitalize()}
- **Board**: {board_str if board_str else 'No community cards yet'}
- **Amount to Call**: {extracted_data.get('call_amount', 'Unknown')}

- **Blinds**: ${blinds}

## Your Task:
Provide a GTO-based recommendation. Consider:
1. Pot odds and equity
2. Position advantage (who is IP/OOP)
3. Villain's {villain_action} range from {villain_position}
4. Hero's hand strength and equity against that range
5. Stack-to-pot ratio (SPR)
6. Implied odds and fold equity

## Output JSON Format:
{{
  "recommendation": "Fold / Call / Raise to $X",
  "reasoning": "Brief GTO explanation (2-3 sentences)",
  "pot_odds": "X:1 or X%",
  "hand_equity": "X% vs villain range",
  "gto_frequency": "Fold X%, Call Y%, Raise Z%",
  "key_factors": ["Factor 1", "Factor 2", "Factor 3"]
}}

Provide clear, actionable GTO advice."""

    return prompt


class DeepGTOAnalyzer:
    """
    Deep Mode using Claude 3 Opus for heads-up GTO analysis
    Requires manual position inputs for controlled analysis
    """
    
    def __init__(self):
        """Initialize Claude 3 Opus"""
        self.client = anthropic_client
        logger.info("✅ Deep Mode initialized (Claude 3 Opus - Heads-Up GTO)")
    
    def analyze(self, image_data: bytes, hero_position: str, villain_position: str, 
                blinds: str, villain_action: str) -> Dict[str, Any]:
        """
        Analyze heads-up poker situation with manual inputs
        
        Args:
            image_data: Raw image bytes
            hero_position: Hero's position (BTN, SB, BB, etc.)
            villain_position: Villain's position
            blinds: Blind structure (e.g., "0.02/0.05")
            villain_action: What villain did (checked, raised, check-raised, re-raised)
            
        Returns:
            Dictionary with GTO recommendation
        """
        if not ANTHROPIC_API_KEY:
            logger.error("❌ ANTHROPIC_API_KEY not configured!")
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY not configured."
            }
        
        try:
            logger.info(f"🧠 Deep Mode: Analyzing {hero_position} vs {villain_position} (villain {villain_action})")
            
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # STEP 1: Extract game state from image
            extraction_prompt = build_extraction_prompt(hero_position, villain_position, villain_action, blinds)
            
            logger.info("📸 Step 1: Extracting game state...")
            extraction_response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2048,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": extraction_prompt
                            }
                        ]
                    }
                ]
            )
            
            extracted_text = extraction_response.content[0].text.strip()
            extracted_data = self._parse_json(extracted_text)
            
            if not extracted_data.get("success"):
                return {
                    "success": False,
                    "error": "Failed to extract game state from image"
                }
            
            logger.info(f"✅ Extracted: Pot={extracted_data.get('pot_size')}, Cards={extracted_data.get('hero_cards')}")
            
            # STEP 2: Get GTO recommendation
            gto_prompt = build_gto_prompt(extracted_data, hero_position, villain_position, villain_action, blinds)
            
            logger.info("🎯 Step 2: Getting GTO recommendation...")
            gto_response = self.client.messages.create(
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
            
            gto_text = gto_response.content[0].text.strip()
            gto_data = self._parse_json(gto_text)
            
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
            logger.error(f"❌ Deep Mode error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_json(self, text: str) -> Dict:
        """Parse JSON from Claude response"""
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
