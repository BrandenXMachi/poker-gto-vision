"""
Flop GTO Analyzer
Uses Gemini Flash for visual extraction + comprehensive flop decision logic
"""

import os
import json
import logging
from typing import Dict, Any, List
import google.generativeai as genai
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API configured for Flop Mode")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set")


def build_gemini_flop_prompt():
    """Build Gemini prompt for flop visual extraction only"""
    return """You are analyzing a poker table screenshot for FLOP decision-making.

## EXTRACT ONLY:

1. **HERO'S HOLE CARDS** (2 cards at bottom):
   - Format: "Rank of Suit" (e.g., "Ace of Spades", "King of Hearts")

2. **FLOP CARDS** (3 community cards):
   - Format: ["Card1", "Card2", "Card3"]
   - Example: ["Ace of Spades", "King of Diamonds", "9 of Hearts"]

## Output Format (JSON ONLY):
{
  "success": true,
  "hero_cards": ["Ace of Spades", "King of Hearts"],
  "flop_cards": ["8 of Diamonds", "6 of Diamonds", "9 of Hearts"]
}

**CRITICAL:**
1. Extract EXACTLY 2 hero cards
2. Extract EXACTLY 3 flop cards
3. Be precise with suits (♠♥♦♣)
4. Output ONLY valid JSON"""


class FlopGTOAnalyzer:
    """
    Flop Mode: Gemini extracts cards + Comprehensive flop GTO decision logic
    """
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Flop GTO Analyzer initialized")
    
    def analyze(self, 
                image_data: bytes,
                hero_position: str,  # "IP" or "OOP"
                preflop_action: str,  # "villain_called", "villain_3bet", "villain_opened", "villain_4bet"
                villain_position: str,  # "UTG", "MP", "CO", "BTN", "SB", "BB"
                blinds: str) -> Dict[str, Any]:
        """
        Analyze flop situation with comprehensive GTO logic
        
        Args:
            image_data: Raw image bytes
            hero_position: "IP" (in position) or "OOP" (out of position)
            preflop_action: Villain's preflop action
            villain_position: Villain's position
            blinds: Blind structure
            
        Returns:
            Flop GTO recommendation
        """
        if not GEMINI_API_KEY:
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured"
            }
        
        try:
            logger.info(f"🎴 Flop Mode: Position={hero_position}, Preflop={preflop_action}, Villain={villain_position}")
            
            # STEP 1: Gemini extracts visual data
            image = Image.open(BytesIO(image_data))
            prompt = build_gemini_flop_prompt()
            
            response = self.model.generate_content([prompt, image])
            result_text = response.text.strip()
            
            # Clean JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result_text = result_text.strip()
            extracted = json.loads(result_text)
            
            if not extracted.get("success"):
                return {"success": False, "error": "Failed to extract visual data"}
            
            hero_cards = extracted.get("hero_cards", [])
            flop_cards = extracted.get("flop_cards", [])
            
            if len(hero_cards) != 2 or len(flop_cards) != 3:
                return {"success": False, "error": "Could not detect 2 hero cards and 3 flop cards"}
            
            logger.info(f"✅ Extracted: Hero={hero_cards}, Flop={flop_cards}")
            
            # STEP 2: Classify hand strength and board texture
            hand_strength = self._classify_hand_strength(hero_cards, flop_cards)
            board_texture = self._classify_board_texture(flop_cards)
            villain_range_type = self._classify_villain_range(villain_position)
            
            # STEP 3: Apply comprehensive flop GTO logic
            decision = self._make_flop_decision(
                preflop_action=preflop_action,
                hero_position=hero_position,
                villain_range_type=villain_range_type,
                hand_strength=hand_strength,
                board_texture=board_texture
            )
            
            logger.info(f"✅ Flop Decision: {decision['action']}")
            
            return {
                "success": True,
                "extracted_data": {
                    "hero_cards": hero_cards,
                    "flop_cards": flop_cards,
                    "hand_strength": hand_strength,
                    "board_texture": board_texture,
                    "villain_range": villain_range_type
                },
                "recommendation": decision
            }
            
        except Exception as e:
            logger.error(f"❌ Flop analysis error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _classify_hand_strength(self, hero_cards: List[str], flop_cards: List[str]) -> str:
        """Classify hero's hand strength on the flop"""
        # Simplified classification - in production, use proper hand evaluator
        # Returns: "monster", "strong", "medium", "weak", "draw"
        # TODO: Implement proper hand evaluation logic
        return "strong"  # Placeholder
    
    def _classify_board_texture(self, flop_cards: List[str]) -> str:
        """Classify board as dry or wet"""
        # Simplified classification
        # Returns: "dry" or "wet"
        # TODO: Implement proper board texture analysis
        return "dry"  # Placeholder
    
    def _classify_villain_range(self, villain_position: str) -> str:
        """Classify villain range type based on position"""
        if villain_position in ["UTG", "MP"]:
            return "early"  # Tight, strong, condensed
        elif villain_position in ["CO", "BTN"]:
            return "late"  # Wide, polarized
        else:  # SB, BB
            return "blinds"  # Capped, medium-strength
    
    def _make_flop_decision(self,
                           preflop_action: str,
                           hero_position: str,
                           villain_range_type: str,
                           hand_strength: str,
                           board_texture: str) -> Dict[str, Any]:
        """
        Comprehensive flop decision logic based on preflop line, position, and hand strength
        """
        
        # STATE 1: Villain called hero's open (SRP)
        if preflop_action == "villain_called":
            return self._villain_called_hero_open(hero_position, villain_range_type, hand_strength, board_texture)
        
        # STATE 2: Villain called hero's 3-bet (3-bet pot - villain flatted)
        elif preflop_action == "villain_called_3bet":
            return self._villain_called_hero_3bet(hero_position, villain_range_type, hand_strength, board_texture)
        
        # STATE 3: Villain 3-bet hero's open and hero called
        elif preflop_action == "villain_3bet":
            return self._villain_3bet_hero_called(hero_position, villain_range_type, hand_strength, board_texture)
        
        # STATE 4: Villain open-raised and hero called
        elif preflop_action == "villain_opened":
            return self._villain_opened_hero_called(hero_position, villain_range_type, hand_strength, board_texture)
        
        # STATE 5: Villain 4-bet and hero called
        elif preflop_action == "villain_4bet":
            return self._villain_4bet_hero_called(hero_position, villain_range_type, hand_strength, board_texture)
        
        else:
            return {
                "action": "Check",
                "reasoning": "Unknown preflop action"
            }
    
    def _villain_called_hero_open(self, hero_pos: str, villain_range: str, hand_str: str, board: str) -> Dict[str, Any]:
        """Hero has range advantage - villain called hero's open"""
        
        if hero_pos == "IP":
            # In position - hero has initiative
            if hand_str == "monster":
                if board == "dry":
                    return {"action": "Bet 25-33% pot", "reasoning": "Monster on dry board IP - bet small"}
                else:
                    return {"action": "Bet 60-75% pot", "reasoning": "Monster on wet board IP - size up"}
            
            elif hand_str == "strong":
                if board == "dry":
                    return {"action": "Bet 33% pot", "reasoning": "Strong hand dry board - small bet"}
                else:
                    return {"action": "Bet 60% pot", "reasoning": "Strong hand wet board - protect"}
            
            elif hand_str == "medium":
                return {"action": "Check back", "reasoning": "Medium strength - check back for pot control"}
            
            elif hand_str == "draw":
                if board == "dry":
                    return {"action": "Check back or bet 25%", "reasoning": "Draw on dry board - selective bluff"}
                else:
                    return {"action": "Bet 75% pot", "reasoning": "Strong draw wet board - semi-bluff big"}
            
            else:  # weak
                if board == "dry":
                    return {"action": "Check back", "reasoning": "Weak hand - give up"}
                else:
                    return {"action": "Check back", "reasoning": "Weak hand - no bluff"}
        
        else:  # OOP
            # Out of position - more defensive
            if hand_str == "monster":
                return {"action": "Check-raise 3x villain bet", "reasoning": "Monster OOP - trap with check-raise"}
            
            elif hand_str == "strong":
                return {"action": "Check-call limit 75% pot", "reasoning": "Strong hand OOP - check-call"}
            
            elif hand_str == "medium":
                return {"action": "Check-fold", "reasoning": "Medium hand OOP - too weak to continue"}
            
            elif hand_str == "draw":
                return {"action": "Check-raise 3-4x villain bet", "reasoning": "Strong draw OOP - check-raise semi-bluff"}
            
            else:  # weak
                return {"action": "Check-fold", "reasoning": "Weak hand OOP - fold to pressure"}
    
    def _villain_called_hero_3bet(self, hero_pos: str, villain_range: str, hand_str: str, board: str) -> Dict[str, Any]:
        """Hero 3-bet, villain called (3-bet pot) - Villain has very strong, condensed range"""
        
        if hero_pos == "IP":
            # In position after 3-betting
            if hand_str == "monster":
                if board == "dry":
                    return {"action": "Bet 33% pot", "reasoning": "Monster in 3bet pot IP dry - small value bet"}
                else:
                    return {"action": "Bet 75% pot", "reasoning": "Monster in 3bet pot IP wet - large value bet"}
            
            elif hand_str == "strong":
                if board == "dry":
                    return {"action": "Bet 40% pot", "reasoning": "Strong in 3bet pot IP dry - medium bet"}
                else:
                    return {"action": "Bet 60% pot", "reasoning": "Strong in 3bet pot IP wet - protect"}
            
            elif hand_str == "medium":
                return {"action": "Check back", "reasoning": "Medium in 3bet pot IP - too weak to bet, pot control"}
            
            elif hand_str == "draw":
                if board == "wet":
                    return {"action": "Bet 75% pot", "reasoning": "Strong draw in 3bet pot IP - aggressive semi-bluff"}
                else:
                    return {"action": "Check back", "reasoning": "Weak draw in 3bet pot IP - give up"}
            
            else:  # weak
                return {"action": "Check back", "reasoning": "Weak in 3bet pot IP - check and fold to bet"}
        
        else:  # OOP
            # Out of position after 3-betting - very cautious
            if hand_str == "monster":
                return {"action": "Bet 50% pot or check-raise 3x", "reasoning": "Monster in 3bet pot OOP - bet for value or trap"}
            
            elif hand_str == "strong":
                return {"action": "Check-call limit 75% pot", "reasoning": "Strong in 3bet pot OOP - check-call cautiously"}
            
            elif hand_str == "medium":
                return {"action": "Check-fold", "reasoning": "Medium in 3bet pot OOP - too weak vs villain's strong range"}
            
            elif hand_str == "draw":
                return {"action": "Check-raise 3.5x (nut draws only)", "reasoning": "Nut draw in 3bet pot OOP - aggressive check-raise"}
            
            else:  # weak
                return {"action": "Check-fold", "reasoning": "Weak in 3bet pot OOP - give up immediately"}
    
    def _villain_3bet_hero_called(self, hero_pos: str, villain_range: str, hand_str: str, board: str) -> Dict[str, Any]:
        """Hero's range is capped - villain 3-bet and hero called"""
        
        if hero_pos == "IP":
            if hand_str == "monster":
                if board == "dry":
                    return {"action": "Check back", "reasoning": "Monster vs 3bet IP - slowplay dry board"}
                else:
                    return {"action": "Call", "reasoning": "Monster vs 3bet - call and re-evaluate turn"}
            
            elif hand_str == "strong":
                if board == "dry":
                    return {"action": "Check back", "reasoning": "Strong vs 3bet dry - check back"}
                else:
                    return {"action": "Check-call small bets only", "reasoning": "Strong vs 3bet wet - check-call small"}
            
            elif hand_str == "medium":
                return {"action": "Check-call small bets (≤40% pot)", "reasoning": "Medium vs 3bet - only call very small"}
            
            elif hand_str == "draw":
                return {"action": "Check-call", "reasoning": "Draw vs 3bet - check-call"}
            
            else:  # weak
                return {"action": "Check-fold", "reasoning": "Weak vs 3bet - fold"}
        
        else:  # OOP
            if hand_str == "monster":
                return {"action": "Check-raise 3.5-4x villain bet", "reasoning": "Monster vs 3bet OOP - check-raise"}
            
            elif hand_str == "strong":
                return {"action": "Check-call limit 60% pot", "reasoning": "Strong vs 3bet OOP - check-call tight"}
            
            elif hand_str == "medium":
                return {"action": "Check-fold", "reasoning": "Medium vs 3bet OOP - too weak"}
            
            elif hand_str == "draw":
                return {"action": "Check-raise 4x villain bet", "reasoning": "Strong draw vs 3bet OOP - check-raise combo"}
            
            else:  # weak
                return {"action": "Check-fold", "reasoning": "Weak vs 3bet OOP - fold"}
    
    def _villain_opened_hero_called(self, hero_pos: str, villain_range: str, hand_str: str, board: str) -> Dict[str, Any]:
        """Villain has initiative and range advantage"""
        
        # Adjust strategy based on villain range
        early_position = (villain_range == "early")
        
        if hero_pos == "OOP":
            if hand_str == "monster":
                return {"action": "Check-raise 2.5x villain bet", "reasoning": "Monster vs villain open OOP - check-raise"}
            
            elif hand_str == "strong":
                if early_position:
                    return {"action": "Check-call limit 50% pot", "reasoning": "Strong vs early open OOP - tight check-call"}
                else:
                    return {"action": "Check-call limit 75% pot", "reasoning": "Strong vs late open OOP - wider check-call"}
            
            elif hand_str == "medium":
                if early_position:
                    return {"action": "Check-fold", "reasoning": "Medium vs early open OOP - fold"}
                else:
                    return {"action": "Check-call limit 33% pot", "reasoning": "Medium vs late open OOP - call small only"}
            
            elif hand_str == "draw":
                return {"action": "Check-raise 3x villain bet", "reasoning": "Draw vs open OOP - semi-bluff check-raise"}
            
            else:  # weak
                return {"action": "Check-fold", "reasoning": "Weak vs open OOP - fold"}
        
        else:  # IP
            if hand_str == "monster":
                if board == "wet":
                    return {"action": "Raise 3x villain bet", "reasoning": "Monster vs open IP wet - raise"}
                else:
                    return {"action": "Call", "reasoning": "Monster vs open IP dry - call"}
            
            elif hand_str == "strong":
                return {"action": "Call", "reasoning": "Strong vs open IP - call"}
            
            elif hand_str == "medium":
                if early_position:
                    return {"action": "Fold", "reasoning": "Medium vs early open IP - fold"}
                else:
                    return {"action": "Float (call)", "reasoning": "Medium vs late open IP - float"}
            
            elif hand_str == "draw":
                if board == "wet" and not early_position:
                    return {"action": "Raise 3x villain bet", "reasoning": "Combo draw vs late open IP - semi-bluff raise"}
                else:
                    return {"action": "Call", "reasoning": "Draw vs open IP - call"}
            
            else:  # weak
                return {"action": "Fold", "reasoning": "Weak vs open IP - fold"}
    
    def _villain_4bet_hero_called(self, hero_pos: str, villain_range: str, hand_str: str, board: str) -> Dict[str, Any]:
        """Extremely narrow ranges - villain 4-bet"""
        
        if hero_pos == "OOP":
            if hand_str == "monster":
                return {"action": "Check-raise 3x villain bet", "reasoning": "Monster vs 4bet OOP - check-raise value"}
            
            elif hand_str == "strong":
                return {"action": "Check-call limit 60% pot", "reasoning": "Strong vs 4bet OOP - tight check-call"}
            
            elif hand_str == "draw":
                return {"action": "Check-raise 4x villain bet (nuts draws only)", "reasoning": "Nut draw vs 4bet OOP - check-raise"}
            
            else:  # medium or weak
                return {"action": "Check-fold", "reasoning": "Not strong enough vs 4bet OOP - fold"}
        
        else:  # IP
            if hand_str == "monster":
                return {"action": "Call", "reasoning": "Monster vs 4bet IP - call"}
            
            elif hand_str == "strong":
                return {"action": "Call", "reasoning": "Strong vs 4bet IP - call"}
            
            elif hand_str == "draw":
                return {"action": "Check-call (nut draws only)", "reasoning": "Nut draw vs 4bet IP - call"}
            
            else:  # medium or weak
                return {"action": "Check-fold", "reasoning": "Not strong enough vs 4bet IP - fold"}
