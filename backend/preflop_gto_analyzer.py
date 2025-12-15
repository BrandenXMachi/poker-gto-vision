"""
Preflop GTO Analyzer
Uses Gemini for visual extraction + custom GTO algorithm for preflop decisions
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple
import google.generativeai as genai
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API configured for Preflop Mode")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set")


# GTO Preflop Ranges
OPENING_RANGES = {
    "UTG": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AKs", "AQs", "AJs", "ATs", "AKo", "AQo", "KQs", "QJs", "JTs"],
    "MP": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "AKs", "AQs", "AJs", "ATs", "A9s", "AKo", "AQo", "AJo", "KQs", "KJs", "QJs", "T9s", "98s"],
    "CO": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "AKo", "AQo", "AJo", "ATo", "KQs", "KJs", "KTs", "QJs", "QTs", "JTs", "T9s", "98s", "87s", "KQo"],
    "BTN": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "AKo", "AQo", "AJo", "ATo", "A9o", "KQs", "KJs", "KTs", "K9s", "K8s", "KQo", "KJo", "QJs", "QTs", "Q9s", "QJo", "JTs", "J9s", "J8s", "T9s", "T8s", "98s", "97s", "87s", "86s", "76s", "75s", "65s", "54s"],
    "SB": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "AKo", "AQo", "AJo", "ATo", "KQs", "KJs", "KTs", "QJs", "QTs", "JTs", "T9s", "98s", "87s", "76s"]
}

CALLING_VS_OPEN = {
    "MP_vs_UTG": ["22", "33", "44", "55", "66", "77", "88", "99", "ATs", "AJs", "AQs", "KQs", "QJs", "JTs", "T9s"],
    "CO_vs_UTG": ["22", "33", "44", "55", "66", "77", "88", "99", "ATs", "AJs", "AQs", "KQs", "QJs", "JTs", "T9s"],
    "BTN_vs_UTG": ["22", "33", "44", "55", "66", "77", "88", "99", "ATs", "AJs", "AQs", "KQs", "QJs", "JTs", "T9s"],
    "CO_vs_MP": ["22", "33", "44", "55", "66", "77", "88", "99", "ATs", "AJs", "AQs", "AQo", "AJo", "KQs", "KJs", "QJs", "JTs", "T9s", "98s"],
    "BTN_vs_MP": ["22", "33", "44", "55", "66", "77", "88", "99", "ATs", "AJs", "AQs", "AQo", "AJo", "KQs", "KJs", "QJs", "JTs", "T9s", "98s"],
    "BTN_vs_CO": ["22", "33", "44", "55", "66", "77", "88", "A7s", "A8s", "A9s", "ATs", "AJs", "AQs", "ATo", "AJo", "AQo", "KQs", "KJs", "KTs", "QJs", "QTs", "JTs", "T9s", "98s", "87s"],
    "SB_vs_BTN": ["22", "33", "44", "55", "66", "77", "A2s", "A3s", "A4s", "A5s", "A9s", "ATs", "AJs", "KQs", "KJs", "QJs", "JTs", "T9s", "98s"],
    "BB_vs_BTN": ["22", "33", "44", "55", "66", "77", "88", "99", "A2s", "A3s", "A4s", "A5s", "A6s", "A7s", "A8s", "A9s", "ATs", "AJs", "A9o", "ATo", "AJo", "AQo", "K9s", "KTs", "KJs", "KJo", "KQo", "Q9s", "QTs", "QJs", "J9s", "JTs", "T9s", "98s", "87s", "76s"]
}

CALLING_VS_3BET = {
    "UTG": ["JJ", "QQ", "AKs", "AQs"],
    "MP": ["TT", "JJ", "QQ", "AKs", "AQs"],
    "CO": ["99", "TT", "JJ", "QQ", "AKs", "AQs", "AJs", "KQs"],
    "BTN": ["88", "99", "TT", "JJ", "QQ", "AKs", "AQs", "AJs", "ATs", "KQs", "QJs", "JTs"],
    "SB": ["77", "88", "99", "TT", "JJ", "QQ", "ATs", "AJs", "AQs", "AJo", "AQo", "AKo", "KQs", "KJs", "QJs", "JTs"]
}

THREEBET_RANGES = {
    "MP_vs_UTG": ["AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"],
    "MP_vs_MP": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "MP_vs_CO": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "MP_vs_BTN": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "CO_vs_UTG": ["AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"],
    "CO_vs_MP": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "CO_vs_CO": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "CO_vs_BTN": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "ATs", "KQs"],
    "BTN_vs_UTG": ["AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"],
    "BTN_vs_MP": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "BTN_vs_CO": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "KQs"],
    "BTN_vs_BTN": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "ATs", "KQs", "QJs"],
    "SB_vs_UTG": ["AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"],
    "SB_vs_MP": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "SB_vs_CO": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "KQs"],
    "SB_vs_BTN": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "ATs", "KQs", "QJs"],
    "BB_vs_UTG": ["AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"],
    "BB_vs_MP": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs"],
    "BB_vs_CO": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "KQs"],
    "BB_vs_BTN": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "ATs", "KQs", "QJs"],
    "BB_vs_SB": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AJs", "ATs"]
}

FOURBET_RANGES = {
    "MP_vs_UTG": ["AA", "KK", "AKs", "AKo"],
    "MP_vs_MP": ["AA", "KK", "AKs", "AKo"],
    "MP_vs_CO": ["AA", "KK", "QQ", "AKs", "AKo"],
    "MP_vs_BTN": ["AA", "KK", "QQ", "AKs", "AKo"],
    "CO_vs_UTG": ["AA", "KK", "AKs", "AKo"],
    "CO_vs_MP": ["AA", "KK", "AKs", "AKo"],
    "CO_vs_CO": ["AA", "KK", "AKs", "AKo"],
    "CO_vs_BTN": ["AA", "KK", "QQ", "AKs", "AKo"],
    "BTN_vs_UTG": ["AA", "KK", "AKs", "AKo"],
    "BTN_vs_MP": ["AA", "KK", "AKs", "AKo"],
    "BTN_vs_CO": ["AA", "KK", "QQ", "AKs", "AKo"],
    "BTN_vs_BTN": ["AA", "KK", "QQ", "AKs", "AKo"],
    "SB_vs_UTG": ["AA", "KK", "AKs", "AKo"],
    "SB_vs_MP": ["AA", "KK", "AKs", "AKo"],
    "SB_vs_CO": ["AA", "KK", "QQ", "AKs", "AKo"],
    "SB_vs_BTN": ["AA", "KK", "QQ", "AKs", "AKo"],
    "BB_vs_UTG": ["AA", "KK", "AKs", "AKo"],
    "BB_vs_MP": ["AA", "KK", "AKs", "AKo"],
    "BB_vs_CO": ["AA", "KK", "QQ", "AKs", "AKo"],
    "BB_vs_BTN": ["AA", "KK", "QQ", "AKs", "AKo"],
    "BB_vs_SB": ["AA", "KK", "AKs", "AKo"]
}


def build_gemini_preflop_prompt():
    """Build Gemini prompt for preflop visual extraction only"""
    return """You are analyzing a poker table screenshot for PREFLOP decision-making.

## CRITICAL - Card Identification Instructions:

### How to Identify Cards ACCURATELY:
1. **Ranks**: A (Ace), K (King), Q (Queen), J (Jack), T (Ten), 9, 8, 7, 6, 5, 4, 3, 2
2. **Suits**: Look at the symbol carefully:
   - ♠ = Spades (black, upside-down heart shape)
   - ♥ = Hearts (red, heart shape)
   - ♦ = Diamonds (red, diamond shape)
   - ♣ = Clubs (black, clover/trefoil shape)
3. **Pay attention to COLOR**:
   - RED suits = Hearts, Diamonds
   - BLACK suits = Spades, Clubs

## Extract ONLY These Values:

1. **HERO'S HOLE CARDS** (2 cards at bottom - BE PRECISE!):
   - Format: "Rank of Suit" (e.g., "Ace of Spades", "King of Hearts")

2. **POT SIZE**: Look for "Total Pot: $X.XX" or "Pot: $X.XX"

3. **CALL AMOUNT**: Look at action buttons - "Call $X.XX" shows amount to call
   - CRITICAL: Extract the exact dollar amount to call

4. **BOARD CARDS**: Community cards (should be EMPTY for preflop - if you see any, list them)

## Output Format (JSON ONLY):
{{
  "success": true,
  "hero_cards": ["Ace of Spades", "King of Hearts"],
  "pot_size": "$0.15",
  "call_amount": "$0.10",
  "board_cards": []
}}

**CRITICAL RULES:**
1. hero_cards MUST have exactly 2 cards
2. call_amount is the $ to call from buttons
3. board_cards should be [] for preflop
4. Output ONLY valid JSON"""


def parse_hand_notation(card1: str, card2: str) -> str:
    """
    Convert two card descriptions to poker notation (e.g., "AKs", "KQo", "77")
    
    Args:
        card1: "Ace of Spades"
        card2: "King of Hearts"
    
    Returns:
        Hand notation like "AKs", "KQo", "AA", etc.
    """
    rank_map = {
        "Ace": "A", "King": "K", "Queen": "Q", "Jack": "J", "Ten": "T",
        "10": "T", "9": "9", "8": "8", "7": "7", "6": "6", "5": "5",
        "4": "4", "3": "3", "2": "2"
    }
    
    suit_map = {
        "Spades": "s", "Hearts": "h", "Diamonds": "d", "Clubs": "c"
    }
    
    # Parse card 1
    parts1 = card1.split(" of ")
    rank1 = rank_map.get(parts1[0], parts1[0][0].upper())
    suit1 = suit_map.get(parts1[1], "?") if len(parts1) > 1 else "?"
    
    # Parse card 2
    parts2 = card2.split(" of ")
    rank2 = rank_map.get(parts2[0], parts2[0][0].upper())
    suit2 = suit_map.get(parts2[1], "?") if len(parts2) > 1 else "?"
    
    # Build notation
    if rank1 == rank2:
        # Pocket pair
        return f"{rank1}{rank2}"
    else:
        # Sort by rank strength
        rank_order = "AKQJT98765432"
        if rank_order.index(rank1) < rank_order.index(rank2):
            higher, lower = rank1, rank2
            suited = "s" if suit1 == suit2 else "o"
        else:
            higher, lower = rank2, rank1
            suited = "s" if suit1 == suit2 else "o"
        
        return f"{higher}{lower}{suited}"


def detect_action_type(call_amount: float, bb_size: float) -> str:
    """
    Detect if facing an open raise, 3bet, or 4bet based on call amount relative to BB
    
    Args:
        call_amount: Amount to call in dollars
        bb_size: Big blind size in dollars
    
    Returns:
        "open", "3bet", or "4bet"
    """
    ratio = call_amount / bb_size
    
    if ratio <= 4.0:
        return "open"  # 2-4x BB is typically an open raise
    elif ratio <= 12.0:
        return "3bet"   # >4x BB but <12x is typically a 3bet
    else:
        return "4bet"   # Very large bets are 4bets or higher


def check_hand_in_range(hand: str, hand_range: List[str]) -> bool:
    """Check if a hand is in a given range"""
    return hand in hand_range


class PreflopGTOAnalyzer:
    """
    Preflop Mode: Gemini extracts visuals + Custom GTO algorithm makes decision
    """
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Preflop GTO Analyzer initialized")
    
    def analyze(self, image_data: bytes, position: str, villain_position: str, blinds: str) -> Dict[str, Any]:
        """
        Analyze preflop situation
        
        Args:
            image_data: Raw image bytes
            position: Hero's position (BTN, SB, BB, UTG, MP, CO)
            villain_position: Villain's position (BTN, SB, BB, UTG, MP, CO)
            blinds: Blind structure (e.g., "0.02/0.05")
            
        Returns:
            GTO preflop recommendation
        """
        if not GEMINI_API_KEY:
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured"
            }
        
        try:
            logger.info(f"🎯 Preflop Mode: Position={position}, Blinds={blinds}")
            
            # Extract BB size
            sb_str, bb_str = blinds.split("/")
            bb_size = float(bb_str)
            
            # STEP 1: Gemini extracts visual data
            logger.info("👁️ Gemini extracting visual data...")
            
            image = Image.open(BytesIO(image_data))
            prompt = build_gemini_preflop_prompt()
            
            response = self.model.generate_content([prompt, image])
            result_text = response.text.strip()
            
            # Clean JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            extracted = json.loads(result_text)
            
            if not extracted.get("success"):
                return {"success": False, "error": "Failed to extract visual data"}
            
            hero_cards = extracted.get("hero_cards", [])
            if len(hero_cards) != 2:
                return {"success": False, "error": "Could not detect 2 hero cards"}
            
            # Parse hand notation
            hand_notation = parse_hand_notation(hero_cards[0], hero_cards[1])
            
            # Extract call amount
            call_amount_str = extracted.get("call_amount", "$0")
            call_amount = float(call_amount_str.replace("$", ""))
            
            pot_size = extracted.get("pot_size", "$0")
            
            logger.info(f"✅ Extracted: Hand={hand_notation}, CallAmount=${call_amount}, Pot={pot_size}")
            
            # STEP 2: Determine action type (open, 3bet, 4bet)
            action_type = detect_action_type(call_amount, bb_size)
            logger.info(f"📊 Detected action type: {action_type}")
            
            # STEP 3: Apply GTO ranges WITH villain position
            decision = self._make_gto_decision(hand_notation, position, villain_position, action_type)
            
            logger.info(f"✅ GTO Decision: {decision['action']}")
            
            # Build detailed info with analysis breakdown
            detailed_reasoning = f"""📊 Analysis Breakdown:

• Hero Position: {position}
• Villain Position: {villain_position}
• Hand: {hand_notation} ({decision.get('hand_strength', 'Unknown')})
• Pot: {pot_size} | Call: {call_amount_str}
• Action Type: {action_type.upper()} (detected from bet sizing)

🎯 GTO Decision:
{decision['reasoning']}

📈 Range Classification: {decision.get('range_match', 'N/A')}"""
            
            return {
                "success": True,
                "extracted_data": {
                    "hero_position": position,
                    "hero_cards": hero_cards,
                    "hand_notation": hand_notation,
                    "board_cards": [],
                    "pot_size_dollars": pot_size,
                    "call_amount": call_amount_str,
                    "street": "preflop",
                    "action_type": action_type
                },
                "recommendation": {
                    "action": decision["action"],
                    "reasoning": detailed_reasoning,
                    "hand_strength": decision.get("hand_strength", "Unknown"),
                    "range_match": decision.get("range_match", "N/A")
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Preflop analysis error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _make_gto_decision(self, hand: str, position: str, villain_position: str, action_type: str) -> Dict[str, Any]:
        """
        Make GTO decision based on hand, position, villain position and action type
        
        Args:
            hand: Hand notation (e.g., "AKs", "77", "KQo")
            position: Hero's position
            villain_position: Villain's position (who raised)
            action_type: "open", "3bet", or "4bet"
            
        Returns:
            Decision dict with action and reasoning
        """
        if action_type == "open":
            # Facing an open raise from VILLAIN - use villain_position for specific range
            # First check if we can 3bet vs this specific villain
            key = f"{position}_vs_{villain_position}"
            if key in THREEBET_RANGES and check_hand_in_range(hand, THREEBET_RANGES[key]):
                return {
                    "action": f"Raise (3-bet recommended)",
                    "reasoning": f"With {hand} from {position} facing {villain_position} open raise, this is in our 3-betting range. Raise to build the pot and apply pressure.",
                    "hand_strength": "Premium 3-bet",
                    "range_match": f"3-bet range vs {villain_position} open"
                }
            
            # Check if we can call vs this specific villain
            if key in CALLING_VS_OPEN and check_hand_in_range(hand, CALLING_VS_OPEN[key]):
                return {
                    "action": "Call",
                    "reasoning": f"With {hand} from {position} facing {villain_position} open raise, this hand has good implied odds and playability. Call to see a flop.",
                    "hand_strength": "Speculative/Medium",
                    "range_match": f"Calling range vs {villain_position} open"
                }
            
            # Otherwise fold
            return {
                "action": "Fold",
                "reasoning": f"With {hand} from {position} facing an open raise, this hand is not strong enough to continue. Fold and wait for a better spot.",
                "hand_strength": "Weak",
                "range_match": "Not in range"
            }
        
        elif action_type == "3bet":
            # Facing a 3bet - check if we should call, 4bet, or fold
            if position in CALLING_VS_3BET and check_hand_in_range(hand, CALLING_VS_3BET[position]):
                return {
                    "action": "Call",
                    "reasoning": f"With {hand} from {position} facing a 3-bet, this hand is strong enough to call but not quite premium enough to 4-bet. Call to see a flop in position.",
                    "hand_strength": "Strong",
                    "range_match": f"Calling 3-bet range from {position}"
                }
            
            # Check 4-bet range
            for aggressor_pos in ["UTG", "MP", "CO", "BTN", "SB"]:
                key = f"{position}_vs_{aggressor_pos}"
                if key in FOURBET_RANGES and check_hand_in_range(hand, FOURBET_RANGES[key]):
                    return {
                        "action": "Raise (4-bet recommended)",
                        "reasoning": f"With {hand} from {position} facing a 3-bet, this is a premium hand that plays well in a 4-bet pot. Raise to build the pot and apply pressure.",
                        "hand_strength": "Premium",
                        "range_match": f"4-bet range vs 3-bet"
                    }
            
            # Otherwise fold
            return {
                "action": "Fold",
                "reasoning": f"With {hand} from {position} facing a 3-bet, this hand is not strong enough to continue against aggression. Fold.",
                "hand_strength": "Medium/Weak",
                "range_match": "Not in range"
            }
        
        elif action_type == "4bet":
            # Facing a 4bet - only continue with absolute premium hands
            premium_hands = ["AA", "KK", "AKs"]
            if hand in premium_hands:
                return {
                    "action": "Call (or 5-bet with AA)",
                    "reasoning": f"With {hand} facing a 4-bet, you have a premium hand. With AA you can 5-bet, with KK/AKs you should generally call.",
                    "hand_strength": "Premium",
                    "range_match": "Top of range"
                }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"With {hand} facing a 4-bet, even though you may have opened or 3-bet, this is too much aggression. Fold and preserve your stack.",
                    "hand_strength": "Not strong enough vs 4-bet",
                    "range_match": "Not in range"
                }
        
        else:
            # Unopened pot - check if we should open (NEVER LIMP)
            if position in OPENING_RANGES and check_hand_in_range(hand, OPENING_RANGES[position]):
                return {
                    "action": "Raise to 3x BB (Open)",
                    "reasoning": f"With {hand} from {position} in an unopened pot, this hand is in the opening range. Raise to 3x BB to build the pot and take the initiative. NEVER limp.",
                    "hand_strength": "Opening range",
                    "range_match": f"Opening range from {position}"
                }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"With {hand} from {position}, this hand is not in the opening range. Fold and wait for a better opportunity. Never complete/limp with weak hands.",
                    "hand_strength": "Below opening range",
                    "range_match": "Not in opening range"
                }
