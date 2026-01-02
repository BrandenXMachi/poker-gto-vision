"""
Turn/River Analyzer
Mathematical decision-making for turn and river situations
Uses Gemini for visual extraction + structured logic for decisions
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from hand_evaluator import evaluate_hand, HandEvaluation, Card

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API configured for Turn/River Mode")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set")


def build_gemini_tr_prompt():
    """Build Gemini prompt for Turn/River visual extraction"""
    return """You are analyzing a poker table screenshot for TURN or RIVER decision-making.

## EXTRACT ONLY These Values:

1. **HERO'S HOLE CARDS** (2 cards at bottom):
   - Format: "Rank of Suit" (e.g., "Ace of Spades", "King of Hearts")

2. **BOARD CARDS** (4 or 5 community cards):
   - Format: ["Card1", "Card2", "Card3", "Card4"] for turn
   - Format: ["Card1", "Card2", "Card3", "Card4", "Card5"] for river
   - Example: ["Queen of Hearts", "Jack of Diamonds", "Ten of Clubs", "4 of Hearts"]

3. **POT SIZE**: Look for "Total Pot: $X.XX" or "Pot: $X.XX"

4. **CALL AMOUNT**: Look at action buttons - "Call $X.XX" shows amount to call
   - If no call amount (checked to you), extract "$0.00"

## Output Format (JSON ONLY):
{{
  "success": true,
  "hero_cards": ["Ace of Spades", "King of Hearts"],
  "board_cards": ["Queen of Hearts", "Jack of Diamonds", "Ten of Clubs", "4 of Hearts"],
  "pot_size": "$10.50",
  "call_amount": "$5.00"
}}

**CRITICAL RULES:**
1. hero_cards MUST have exactly 2 cards
2. board_cards MUST have exactly 4 or 5 cards (turn or river)
3. Extract exact dollar amounts
4. Output ONLY valid JSON"""


class TurnRiverAnalyzer:
    """
    Turn/River Mode: Mathematical analysis for late street decisions
    """
    
    def __init__(self):
        """Initialize Gemini model"""
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Turn/River Analyzer initialized")
    
    def _build_partial_prompt(self):
        """Build simplified Gemini prompt when hero cards + flop already known"""
        return """You are analyzing a poker table for TURN or RIVER.

We ALREADY KNOW the hero's 2 hole cards and the 3 flop cards.

## EXTRACT ONLY:

1. **NEW CARD(S)**: The turn card (1 card) OR turn+river cards (2 cards)
   - DO NOT extract hero cards or flop cards - we already have them
   - Format: "Rank of Suit" (e.g., "8 of Diamonds")
   - For turn: extract 1 new card
   - For river: extract 2 new cards (turn + river)

2. **POT SIZE**: Look for "Total Pot: $X.XX" or "Pot: $X.XX"

3. **CALL AMOUNT**: Look at "Call $X.XX" button
   - If checked to you, use "$0.00"

Output JSON:
{
  "success": true,
  "new_cards": ["8 of Diamonds"],
  "pot_size": "$10.50",
  "call_amount": "$5.00"
}

**IMPORTANT:** Only extract NEW board cards (1-2 cards), not all cards."""
    
    def analyze(self, image_data: bytes, blinds: str = "0.02/0.05",
                hero_cards: List[str] = None, flop_cards: List[str] = None,
                hero_position: str = None, villain_position: str = None,
                flop_action: str = None) -> Dict[str, Any]:
        """
        Analyze turn or river situation
        
        Args:
            image_data: Raw image bytes
            blinds: Blind structure
            hero_cards: Optional - Hero's 2 cards from Flop mode
            flop_cards: Optional - 3 flop cards from Flop mode
            hero_position: Optional - IP/OOP from Flop mode
            villain_position: Optional - Villain position from Flop mode
            flop_action: Optional - Flop action context
            
        Returns:
            Complete analysis with recommendation
        """
        if not GEMINI_API_KEY:
            return {
                "success": False,
                "error": "GEMINI_API_KEY not configured"
            }
        
        try:
            has_context = hero_cards is not None and flop_cards is not None
            logger.info(f"🎴 Turn/River Mode analyzing... Blinds: {blinds}, Has Context: {has_context}")
            
            # Extract BB size
            sb_str, bb_str = blinds.split("/")
            bb_size = float(bb_str)
            
            # STEP 1: Gemini extracts visual data
            image = Image.open(BytesIO(image_data))
            
            # Use simplified prompt if we have context from Flop
            if has_context:
                prompt = self._build_partial_prompt()
                logger.info("✅ Using partial extraction (turn/river card + pot/call only)")
            else:
                prompt = build_gemini_tr_prompt()
                logger.info("📊 Using full extraction (all cards + pot/call)")
            
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
            
            # Handle partial vs full extraction
            if has_context:
                # Partial extraction - combine known cards with new cards
                final_hero_cards = hero_cards  # Use provided hero cards
                new_cards = extracted.get("new_cards", [])
                final_board_cards = flop_cards + new_cards  # Combine flop + turn/river
                
                logger.info(f"✅ Combined cards: Hero={final_hero_cards}, Flop={flop_cards}, New={new_cards}, Total Board={final_board_cards}")
            else:
                # Full extraction - use extracted cards
                final_hero_cards = extracted.get("hero_cards", [])
                final_board_cards = extracted.get("board_cards", [])
            
            pot_size_str = extracted.get("pot_size", "$0")
            call_amount_str = extracted.get("call_amount", "$0")
            
            # Validate
            if len(final_hero_cards) != 2:
                return {"success": False, "error": "Could not detect 2 hero cards"}
            
            if len(final_board_cards) not in [4, 5]:
                return {"success": False, "error": f"Invalid board size: {len(final_board_cards)} cards (need 4 or 5)"}
            
            # Parse amounts
            pot_size = float(pot_size_str.replace("$", ""))
            call_amount = float(call_amount_str.replace("$", ""))
            
            logger.info(f"✅ Extracted: Hero={final_hero_cards}, Board={final_board_cards}, Pot=${pot_size}, Call=${call_amount}")
            
            # STEP 2: Detect street
            street = "turn" if len(final_board_cards) == 4 else "river"
            logger.info(f"📊 Detected street: {street.upper()}")
            
            # STEP 3: Evaluate hand
            evaluation = evaluate_hand(final_hero_cards, final_board_cards)
            
            # STEP 4: Calculate bet sizing category (pot-relative AND BB-relative)
            bet_category, bet_size_bb = self._classify_bet_size(pot_size, call_amount, bb_size)
            
            # STEP 5: Count outs (turn only)
            outs, draw_types = self._count_outs(final_hero_cards, final_board_cards, evaluation, street)
            
            # STEP 6: Calculate equity
            equity = self._calculate_equity(street, outs, evaluation.strength, evaluation)
            
            # STEP 7: Calculate pot odds
            pot_odds = self._calculate_pot_odds(pot_size, call_amount)
            
            # STEP 8: Calculate EV
            ev = self._calculate_ev(equity, pot_size, call_amount, bb_size)
            
            # STEP 9: Make decision
            decision = self._make_decision(
                street=street,
                hand_strength=evaluation.strength,
                outs=outs,
                equity=equity,
                pot_odds=pot_odds,
                bet_category=bet_category,
                board_cards=final_board_cards
            )
            
            logger.info(f"✅ Decision: {decision['action']}")
            
            return {
                "success": True,
                "extracted_data": {
                    "hero_cards": final_hero_cards,
                    "board_cards": final_board_cards,
                    "pot_size": pot_size_str,
                    "call_amount": call_amount_str,
                    "bet_size_bb": f"{bet_size_bb:.1f} BB",
                    "street": street.upper(),
                    "bet_category": bet_category
                },
                "analysis": {
                    "hand_strength": {
                        "made_hand": evaluation.made_hand,
                        "description": evaluation.description,
                        "strength_category": evaluation.strength
                    },
                    "outs": {
                        "count": outs,
                        "types": draw_types
                    },
                    "equity": {
                        "value": f"{equity:.1f}%",
                        "calculation": self._get_equity_explanation(street, outs, evaluation.strength)
                    },
                    "pot_odds": pot_odds,
                    "expected_value": ev
                },
                "recommendation": decision
            }
            
        except Exception as e:
            logger.error(f"❌ Turn/River analysis error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _classify_bet_size(self, pot: float, call_amount: float, bb_size: float) -> Tuple[str, float]:
        """
        Classify bet size for TURN/RIVER play
        Primary: pot-relative sizing (pots are large on turn/river)
        Secondary: BB sizing for additional context
        Returns: (category, bet_size_in_bb)
        """
        if call_amount == 0:
            return "check", 0.0
        
        # Calculate both ratios
        pot_ratio = call_amount / pot
        bb_ratio = call_amount / bb_size
        
        # For turn/river, pot-relative sizing is PRIMARY
        # BB sizing provides secondary context
        
        # Tiny/Blocking bet: < 25% pot
        if pot_ratio < 0.25:
            category = "tiny"
        # Small bet: 25-40% pot
        elif pot_ratio < 0.40:
            category = "small"
        # Medium/Standard bet: 40-70% pot
        elif pot_ratio < 0.70:
            category = "medium"
        # Large bet: 70-100% pot
        elif pot_ratio < 1.0:
            category = "large"
        # Overbet: > pot
        else:
            category = "overbet"
        
        return category, bb_ratio
    
    def _count_outs(self, hero_cards: List[str], board_cards: List[str], evaluation: HandEvaluation, street: str) -> Tuple[int, List[str]]:
        """
        Count outs that improve hand to likely winner
        Only relevant on turn (river has no outs)
        """
        if street == "river":
            return 0, []
        
        outs = 0
        draw_types = []
        
        # Flush draw
        if evaluation.has_flush_draw:
            outs += evaluation.flush_draw_outs
            draw_types.append(f"Flush draw ({evaluation.flush_draw_outs} outs)")
        
        # Straight draw
        if evaluation.has_oesd:
            # Don't double count if also have flush draw
            straight_outs = evaluation.straight_draw_outs
            if evaluation.has_flush_draw:
                straight_outs = max(0, straight_outs - 1)  # Rough discount
            outs += straight_outs
            draw_types.append(f"OESD ({straight_outs} outs)")
        elif evaluation.has_gutshot:
            gutshot_outs = evaluation.straight_draw_outs
            if evaluation.has_flush_draw:
                gutshot_outs = max(0, gutshot_outs - 1)
            outs += gutshot_outs
            draw_types.append(f"Gutshot ({gutshot_outs} outs)")
        
        # Pair to trips (only if we have a pair currently)
        if evaluation.made_hand == "pair" and not evaluation.has_flush_draw and not evaluation.has_oesd:
            outs += 2
            draw_types.append("Pair to trips (2 outs)")
        
        # Two pair to full house
        if evaluation.made_hand == "two_pair":
            outs += 4
            draw_types.append("Full house draw (4 outs)")
        
        return outs, draw_types
    
    def _calculate_equity(self, street: str, outs: int, hand_strength: str, evaluation: HandEvaluation) -> float:
        """
        Calculate hand equity vs single opponent
        Different calculation for turn vs river
        """
        if street == "turn":
            # Turn equity = draw equity + made hand equity
            draw_equity = (outs / 46) * 100 if outs > 0 else 0
            
            # Made hand base equity (vs unknown opponent)
            if hand_strength == "monster":
                made_equity = 85
            elif hand_strength == "strong":
                made_equity = 70
            elif hand_strength == "medium":
                made_equity = 50
            elif hand_strength == "weak":
                made_equity = 30
            else:  # air
                made_equity = 10
            
            # Use higher of draw or made hand equity
            return max(draw_equity, made_equity)
        
        else:  # river
            # No more draws - pure showdown equity
            if hand_strength == "monster":
                return 90
            elif hand_strength == "strong":
                return 75
            elif hand_strength == "medium":
                return 55  # Bluff catcher range
            elif hand_strength == "weak":
                return 35  # Very marginal
            else:  # air
                return 15  # Pure bluff catcher
    
    def _get_equity_explanation(self, street: str, outs: int, hand_strength: str) -> str:
        """Generate explanation for equity calculation"""
        if street == "turn":
            if outs > 0:
                return f"{outs} outs / 46 unseen cards = {outs/46*100:.1f}% draw equity"
            else:
                return f"{hand_strength.capitalize()} made hand estimated equity vs opponent"
        else:
            return f"River showdown equity for {hand_strength} hand vs single opponent"
    
    def _calculate_pot_odds(self, pot: float, call_amount: float) -> Dict[str, Any]:
        """Calculate pot odds"""
        if call_amount == 0:
            return {
                "percent": "0%",
                "ratio": "0:0",
                "getting_price": pot,
                "need_to_call": 0,
                "calculation": "Checked to you - free to see next card"
            }
        
        total_pot_after_call = pot + call_amount
        pot_odds_percent = (call_amount / total_pot_after_call) * 100
        pot_odds_ratio = f"{total_pot_after_call / call_amount:.1f}:1"
        
        return {
            "percent": f"{pot_odds_percent:.1f}%",
            "ratio": pot_odds_ratio,
            "getting_price": total_pot_after_call,
            "need_to_call": call_amount,
            "calculation": f"${call_amount:.2f} to win ${total_pot_after_call:.2f}"
        }
    
    def _calculate_ev(self, equity: float, pot: float, call_amount: float, bb_size: float) -> Dict[str, Any]:
        """Calculate expected value of calling"""
        if call_amount == 0:
            return {
                "value": "$0.00",
                "value_bb": "0 BB",
                "calculation": "Free to check - no EV calculation needed"
            }
        
        ev_dollars = (equity / 100) * pot - call_amount
        ev_bb = ev_dollars / bb_size
        
        return {
            "value": f"${ev_dollars:+.2f}",
            "value_bb": f"{ev_bb:+.1f} BB",
            "calculation": f"({equity:.1f}% × ${pot:.2f}) - ${call_amount:.2f} = ${ev_dollars:+.2f}"
        }
    
    def _make_decision(self, street: str, hand_strength: str, outs: int, equity: float, 
                       pot_odds: Dict, bet_category: str, board_cards: List[str]) -> Dict[str, Any]:
        """
        Make optimal decision based on all factors
        Different logic for turn vs river
        """
        if street == "turn":
            return self._make_turn_decision(hand_strength, outs, equity, pot_odds, bet_category)
        else:
            return self._make_river_decision(hand_strength, equity, pot_odds, bet_category, board_cards)
    
    def _make_turn_decision(self, hand_strength: str, outs: int, equity: float, 
                           pot_odds: Dict, bet_category: str) -> Dict[str, Any]:
        """Turn-specific decision logic"""
        
        pot_odds_percent = float(pot_odds["percent"].replace("%", ""))
        
        # Free to check
        if bet_category == "check":
            return {
                "action": "Check",
                "reasoning": "Free to see river card - always check when given the option."
            }
        
        # Strong made hand
        if hand_strength in ["monster", "strong"]:
            if bet_category in ["small", "medium"]:
                return {
                    "action": "Call",
                    "reasoning": f"{hand_strength.capitalize()} hand getting good price. With {equity:.1f}% equity vs {pot_odds_percent:.1f}% pot odds, this is a clear call."
                }
            else:  # large/overbet
                return {
                    "action": "Call",
                    "reasoning": f"{hand_strength.capitalize()} hand - call even to large bet. You have {equity:.1f}% equity and strong showdown value."
                }
        
        # Drawing hand
        if outs >= 8:  # Good draw (flush draw or OESD+)
            equity_edge = equity - pot_odds_percent
            if equity > pot_odds_percent:
                return {
                    "action": "Call",
                    "reasoning": f"Drawing with {outs} outs ({equity:.1f}% equity) vs {pot_odds_percent:.1f}% pot odds needed. +{equity_edge:.1f}% equity edge makes this profitable."
                }
            elif equity > pot_odds_percent * 0.85:  # Within 15% - close decision
                return {
                    "action": "Call",
                    "reasoning": f"Close decision with {outs} outs. {equity:.1f}% equity vs {pot_odds_percent:.1f}% needed. Slightly -EV but close enough to call."
                }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"Draw not getting right price. Need {pot_odds_percent:.1f}% equity but only have {equity:.1f}% with {outs} outs."
                }
        
        elif outs >= 4:  # Marginal draw (gutshot, pair to trips)
            if equity > pot_odds_percent * 1.1:  # Need 10% safety margin
                return {
                    "action": "Call",
                    "reasoning": f"Marginal draw ({outs} outs) but getting great price. {equity:.1f}% equity vs {pot_odds_percent:.1f}% needed."
                }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"Weak draw ({outs} outs) not getting sufficient price. {equity:.1f}% equity vs {pot_odds_percent:.1f}% needed."
                }
        
        # Medium made hand (no good draw)
        if hand_strength == "medium":
            if bet_category == "small":  # < 33% pot
                return {
                    "action": "Call",
                    "reasoning": f"Medium hand getting great price ({pot_odds_percent:.1f}% pot odds). With {equity:.1f}% equity, this is profitable."
                }
            elif bet_category == "medium" and pot_odds_percent < 40:
                return {
                    "action": "Call",
                    "reasoning": f"Medium hand with {equity:.1f}% equity vs {pot_odds_percent:.1f}% needed. Acceptable price to see river."
                }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"Medium hand facing large bet ({pot_odds_percent:.1f}% pot odds). Not strong enough to continue."
                }
        
        # Weak hand
        if hand_strength == "weak":
            if bet_category == "small" and pot_odds_percent < 25:
                return {
                    "action": "Call",
                    "reasoning": f"Weak hand but insane price ({pot_odds_percent:.1f}% pot odds < 25%). Worth a call as bluff catcher."
                }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"Weak hand not getting bluff-catcher price. Need < 25% pot odds, facing {pot_odds_percent:.1f}%."
                }
        
        # Air/garbage
        return {
            "action": "Fold",
            "reasoning": "No made hand or draw. Easy fold."
        }
    
    def _make_river_decision(self, hand_strength: str, equity: float, pot_odds: Dict, 
                            bet_category: str, board_cards: List[str]) -> Dict[str, Any]:
        """River-specific decision logic"""
        
        pot_odds_percent = float(pot_odds["percent"].replace("%", ""))
        
        # Free to check
        if bet_category == "check":
            return {
                "action": "Check",
                "reasoning": "Free showdown - always check when given the option on river."
            }
        
        # Classify board texture
        board_texture = self._classify_river_board(board_cards)
        
        # Monster/Strong hand
        if hand_strength in ["monster", "strong"]:
            return {
                "action": "Call",
                "reasoning": f"{hand_strength.capitalize()} hand on river with {equity:.1f}% estimated equity. Clear call for value."
            }
        
        # Medium hand (bluff catcher territory)
        if hand_strength == "medium":
            if bet_category == "small":  # < 33% pot
                return {
                    "action": "Call",
                    "reasoning": f"Medium hand getting great price ({pot_odds_percent:.1f}% pot odds). Good spot to call as bluff catcher."
                }
            elif bet_category == "medium" and pot_odds_percent < 40:
                if board_texture == "dry":
                    return {
                        "action": "Call",
                        "reasoning": f"Medium hand on dry board getting decent price ({pot_odds_percent:.1f}%). Opponent could be bluffing or value betting worse."
                    }
                else:
                    return {
                        "action": "Fold",
                        "reasoning": f"Medium hand on wet board vs medium bet. Too many draws got there - likely beat."
                    }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"Medium hand facing large river bet ({pot_odds_percent:.1f}% pot odds). Not strong enough vs opponent's value range."
                }
        
        # Weak hand (pure bluff catcher)
        if hand_strength == "weak":
            if pot_odds_percent < 25:  # Incredible price
                return {
                    "action": "Call",
                    "reasoning": f"Weak hand but incredible price ({pot_odds_percent:.1f}% < 25%). Opponent needs to be value betting > 75% of the time - worth a call as pure bluff catcher."
                }
            else:
                return {
                    "action": "Fold",
                    "reasoning": f"Weak hand not getting bluff-catcher price. Need < 25% pot odds, facing {pot_odds_percent:.1f}%."
                }
        
        # Air/nothing
        return {
            "action": "Fold",
            "reasoning": "No showdown value on river. Easy fold to any bet."
        }
    
    def _classify_river_board(self, board_cards: List[str]) -> str:
        """Classify river board as dry or wet"""
        try:
            board = [Card(c) for c in board_cards]
            
            # Count suits
            suit_counts = {}
            for card in board:
                suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
            
            # Check for flush possibilities
            if max(suit_counts.values()) >= 3:
                return "wet"
            
            # Check for straight possibilities
            ranks = sorted([c.rank for c in board])
            max_gap = max(ranks) - min(ranks)
            if max_gap <= 4:
                return "wet"
            
            return "dry"
            
        except Exception as e:
            logger.error(f"Board classification error: {e}")
            return "dry"
