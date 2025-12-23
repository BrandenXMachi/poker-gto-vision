"""
Hand Evaluator - Properly evaluates poker hands by connecting hero cards with board cards
Detects made hands, draws, and provides accurate strength classification
"""

from typing import List, Dict, Tuple, Set
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class Card:
    """Represents a single playing card"""
    
    RANK_VALUES = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "Jack": 11, "Queen": 12, "King": 13, "Ace": 14
    }
    
    RANK_NAMES = {v: k for k, v in RANK_VALUES.items()}
    
    SUIT_NAMES = {
        "Spades": "♠", "Hearts": "♥", "Diamonds": "♦", "Clubs": "♣",
        "♠": "Spades", "♥": "Hearts", "♦": "Diamonds", "♣": "Clubs"
    }
    
    def __init__(self, card_string: str):
        """
        Parse card string like "7 of Diamonds" or "Ace of Spades"
        """
        self.original = card_string
        
        # Handle formats: "7 of Diamonds", "Ace of Spades"
        parts = card_string.split(" of ")
        if len(parts) != 2:
            raise ValueError(f"Invalid card format: {card_string}")
        
        rank_str, suit_str = parts[0].strip(), parts[1].strip()
        
        # Parse rank
        if rank_str not in self.RANK_VALUES:
            raise ValueError(f"Invalid rank: {rank_str}")
        
        self.rank = self.RANK_VALUES[rank_str]
        self.rank_name = rank_str
        
        # Parse suit
        self.suit = suit_str
        self.suit_symbol = self.SUIT_NAMES.get(suit_str, suit_str)
    
    def __repr__(self):
        return f"{self.rank_name}{self.suit_symbol}"
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))


class HandEvaluation:
    """Result of hand evaluation"""
    
    def __init__(self):
        self.made_hand = None  # "pair", "two_pair", "trips", "straight", "flush", "full_house", "quads", "straight_flush"
        self.made_hand_rank = 0  # Higher is better
        self.kickers = []  # Kicker values
        
        # Draw information
        self.has_flush_draw = False
        self.flush_draw_outs = 0
        self.has_backdoor_flush_draw = False
        
        self.has_oesd = False  # Open-ended straight draw
        self.has_gutshot = False
        self.straight_draw_outs = 0
        self.has_backdoor_straight_draw = False
        
        # Combo draws
        self.is_combo_draw = False  # Flush draw + straight draw
        
        # Overall classification
        self.strength = "weak"  # "monster", "strong", "medium", "weak", "air"
        
        # Descriptive info
        self.description = ""
        self.draw_description = ""


class HandEvaluator:
    """Evaluates poker hands by properly connecting hero cards with board cards"""
    
    def __init__(self):
        pass
    
    def parse_cards(self, card_strings: List[str]) -> List[Card]:
        """Parse list of card strings into Card objects"""
        cards = []
        for card_str in card_strings:
            try:
                cards.append(Card(card_str))
            except Exception as e:
                logger.error(f"Failed to parse card '{card_str}': {e}")
                raise
        return cards
    
    def evaluate_hand(self, hero_cards: List[str], board_cards: List[str]) -> HandEvaluation:
        """
        Main evaluation function - combines hero cards with board cards
        
        Args:
            hero_cards: List of 2 card strings
            board_cards: List of 3 card strings (flop)
            
        Returns:
            HandEvaluation object with complete analysis
        """
        evaluation = HandEvaluation()
        
        try:
            # Parse cards
            hero = self.parse_cards(hero_cards)
            board = self.parse_cards(board_cards)
            all_cards = hero + board
            
            logger.info(f"Evaluating: Hero={[str(c) for c in hero]}, Board={[str(c) for c in board]}")
            
            # Evaluate made hands
            self._evaluate_made_hands(hero, board, all_cards, evaluation)
            
            # Evaluate draws
            self._evaluate_flush_draws(hero, board, all_cards, evaluation)
            self._evaluate_straight_draws(hero, board, all_cards, evaluation)
            
            # Classify overall strength
            self._classify_strength(evaluation)
            
            # Generate descriptions
            self._generate_descriptions(hero, board, evaluation)
            
            logger.info(f"Result: {evaluation.strength} - {evaluation.description}")
            
        except Exception as e:
            logger.error(f"Hand evaluation error: {e}", exc_info=True)
            evaluation.description = "Error evaluating hand"
            evaluation.strength = "unknown"
        
        return evaluation
    
    def _evaluate_made_hands(self, hero: List[Card], board: List[Card], all_cards: List[Card], eval: HandEvaluation):
        """Evaluate made hands (pairs, trips, straights, flushes, etc.)"""
        
        ranks = [c.rank for c in all_cards]
        rank_counts = Counter(ranks)
        
        # Check for quads
        quads = [r for r, count in rank_counts.items() if count == 4]
        if quads:
            eval.made_hand = "quads"
            eval.made_hand_rank = 700 + max(quads)
            eval.kickers = sorted([r for r in ranks if r not in quads], reverse=True)[:1]
            return
        
        # Check for trips and pairs
        trips = [r for r, count in rank_counts.items() if count == 3]
        pairs = [r for r, count in rank_counts.items() if count == 2]
        
        # Full house
        if trips and pairs:
            eval.made_hand = "full_house"
            eval.made_hand_rank = 600 + max(trips)
            return
        
        # Check for flush
        suit_counts = Counter([c.suit for c in all_cards])
        flush_suit = next((suit for suit, count in suit_counts.items() if count >= 5), None)
        
        if flush_suit:
            flush_cards = sorted([c.rank for c in all_cards if c.suit == flush_suit], reverse=True)[:5]
            # Check for straight flush
            if self._is_straight(flush_cards):
                eval.made_hand = "straight_flush"
                eval.made_hand_rank = 800 + max(flush_cards)
                return
            else:
                eval.made_hand = "flush"
                eval.made_hand_rank = 500 + flush_cards[0]
                eval.kickers = flush_cards[1:5]
                return
        
        # Check for straight
        if self._is_straight(ranks):
            eval.made_hand = "straight"
            eval.made_hand_rank = 400 + max(ranks)
            return
        
        # Trips (no full house)
        if trips:
            eval.made_hand = "trips"
            eval.made_hand_rank = 300 + max(trips)
            eval.kickers = sorted([r for r in ranks if r not in trips], reverse=True)[:2]
            return
        
        # Two pair
        if len(pairs) >= 2:
            top_pairs = sorted(pairs, reverse=True)[:2]
            eval.made_hand = "two_pair"
            eval.made_hand_rank = 200 + top_pairs[0]
            eval.kickers = sorted([r for r in ranks if r not in pairs], reverse=True)[:1]
            return
        
        # One pair
        if pairs:
            pair_rank = max(pairs)
            eval.made_hand = "pair"
            eval.made_hand_rank = 100 + pair_rank
            eval.kickers = sorted([r for r in ranks if r != pair_rank], reverse=True)[:3]
            
            # Check if hero has the pair
            hero_ranks = [c.rank for c in hero]
            if hero_ranks[0] == hero_ranks[1] and hero_ranks[0] == pair_rank:
                eval.has_pocket_pair = True
            return
        
        # High card
        eval.made_hand = "high_card"
        eval.made_hand_rank = max(ranks)
        eval.kickers = sorted(ranks, reverse=True)[1:5]
    
    def _is_straight(self, ranks: List[int]) -> bool:
        """Check if ranks contain a straight"""
        unique_ranks = sorted(set(ranks))
        
        # Check for wheel (A-2-3-4-5)
        if set([14, 2, 3, 4, 5]).issubset(set(unique_ranks)):
            return True
        
        # Check for regular straights
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i+4] - unique_ranks[i] == 4:
                return True
        
        return False
    
    def _evaluate_flush_draws(self, hero: List[Card], board: List[Card], all_cards: List[Card], eval: HandEvaluation):
        """
        Evaluate flush draws - CRITICAL: Hero must have cards of the flush suit!
        """
        # Count suits across ALL cards (hero + board)
        suit_counts = Counter([c.suit for c in all_cards])
        
        # Check each suit
        for suit, count in suit_counts.items():
            # Hero must have at least 1 card of this suit
            hero_suit_count = sum(1 for c in hero if c.suit == suit)
            
            if hero_suit_count == 0:
                continue  # Hero has no cards of this suit - no flush draw possible
            
            # Flush draw: 4 cards of same suit (need 1 more)
            if count == 4:
                eval.has_flush_draw = True
                eval.flush_draw_outs = 9  # 13 - 4 = 9 remaining cards of that suit
                logger.info(f"✅ Flush draw detected: {hero_suit_count} hero cards + board = 4 {suit} cards")
            
            # Backdoor flush draw: 3 cards of same suit (need 2 more)
            elif count == 3:
                eval.has_backdoor_flush_draw = True
                logger.info(f"✅ Backdoor flush draw: {hero_suit_count} hero cards + board = 3 {suit} cards")
    
    def _evaluate_straight_draws(self, hero: List[Card], board: List[Card], all_cards: List[Card], eval: HandEvaluation):
        """
        Evaluate straight draws - Hero's cards must connect with board
        """
        ranks = sorted(set([c.rank for c in all_cards]))
        
        # Check for open-ended straight draw (OESD)
        # Need 4 cards in sequence with gaps at both ends
        oesd_outs = self._count_oesd_outs(ranks)
        if oesd_outs > 0:
            eval.has_oesd = True
            eval.straight_draw_outs += oesd_outs
            logger.info(f"✅ OESD detected: {oesd_outs} outs")
        
        # Check for gutshot (inside straight draw)
        gutshot_outs = self._count_gutshot_outs(ranks)
        if gutshot_outs > 0 and not eval.has_oesd:  # Don't double count
            eval.has_gutshot = True
            eval.straight_draw_outs += gutshot_outs
            logger.info(f"✅ Gutshot detected: {gutshot_outs} outs")
        
        # Check for backdoor straight draw
        if len(ranks) >= 3 and not eval.has_oesd and not eval.has_gutshot:
            if self._has_backdoor_straight_potential(ranks):
                eval.has_backdoor_straight_draw = True
                logger.info(f"✅ Backdoor straight draw potential")
        
        # Combo draw
        if eval.has_flush_draw and (eval.has_oesd or eval.has_gutshot):
            eval.is_combo_draw = True
            logger.info(f"✅ COMBO DRAW! Flush + Straight")
    
    def _count_oesd_outs(self, ranks: List[int]) -> int:
        """Count outs for open-ended straight draw"""
        # Check for 4 cards in sequence
        for i in range(len(ranks) - 3):
            if ranks[i+3] - ranks[i] == 3:  # 4 consecutive ranks
                return 8  # 8 outs (4 cards on each end)
        return 0
    
    def _count_gutshot_outs(self, ranks: List[int]) -> int:
        """Count outs for gutshot straight draw"""
        # Check for 4 cards with one gap
        for i in range(len(ranks) - 3):
            window = ranks[i:i+4]
            if max(window) - min(window) == 4 and len(window) == 4:
                return 4  # 4 outs for the missing card
        return 0
    
    def _has_backdoor_straight_potential(self, ranks: List[int]) -> bool:
        """Check if there's backdoor straight potential"""
        # Simplified: if we have 3+ cards that are reasonably connected
        if len(ranks) < 3:
            return False
        
        # Check if max - min <= 6 (can make straight with 2 cards)
        return max(ranks) - min(ranks) <= 6
    
    def _classify_strength(self, eval: HandEvaluation):
        """Classify overall hand strength"""
        
        # Monster hands
        if eval.made_hand in ["straight_flush", "quads", "full_house"]:
            eval.strength = "monster"
        elif eval.made_hand == "flush":
            eval.strength = "monster"
        elif eval.made_hand == "straight":
            eval.strength = "monster"
        
        # Strong hands
        elif eval.made_hand == "trips":
            eval.strength = "strong"
        elif eval.made_hand == "two_pair":
            eval.strength = "strong"
        
        # Draws can be strong
        elif eval.is_combo_draw:
            eval.strength = "strong"  # Combo draws are very strong
        elif eval.has_flush_draw and eval.has_oesd:
            eval.strength = "strong"
        elif eval.has_flush_draw:
            eval.strength = "medium"  # Flush draw is medium strength
        elif eval.has_oesd:
            eval.strength = "medium"
        
        # Pairs
        elif eval.made_hand == "pair":
            # Check if it's a strong pair (overpair or top pair)
            if eval.made_hand_rank >= 113:  # Pair of Kings or better
                eval.strength = "strong"
            elif eval.made_hand_rank >= 110:  # Pair of Tens or better
                eval.strength = "medium"
            else:
                eval.strength = "weak"  # Low pair
        
        # Gutshot or weak draws
        elif eval.has_gutshot or eval.has_backdoor_flush_draw or eval.has_backdoor_straight_draw:
            eval.strength = "weak"
        
        # Nothing
        else:
            eval.strength = "air"  # Complete air
    
    def _generate_descriptions(self, hero: List[Card], board: List[Card], eval: HandEvaluation):
        """Generate human-readable descriptions"""
        
        # Made hand description
        if eval.made_hand == "pair":
            pair_rank = eval.made_hand_rank - 100
            pair_name = Card.RANK_NAMES.get(pair_rank, str(pair_rank))
            
            # Check if pocket pair
            if hero[0].rank == hero[1].rank and hero[0].rank == pair_rank:
                eval.description = f"Pocket {pair_name}s"
            else:
                # Check if paired with board
                board_ranks = [c.rank for c in board]
                if pair_rank in board_ranks:
                    eval.description = f"Pair of {pair_name}s (paired with board)"
                else:
                    eval.description = f"Pair of {pair_name}s"
        
        elif eval.made_hand == "two_pair":
            eval.description = "Two Pair"
        elif eval.made_hand == "trips":
            eval.description = "Three of a Kind"
        elif eval.made_hand == "straight":
            eval.description = "Straight"
        elif eval.made_hand == "flush":
            eval.description = "Flush"
        elif eval.made_hand == "full_house":
            eval.description = "Full House"
        elif eval.made_hand == "quads":
            eval.description = "Four of a Kind"
        elif eval.made_hand == "straight_flush":
            eval.description = "Straight Flush"
        else:
            high_card = Card.RANK_NAMES.get(eval.made_hand_rank, str(eval.made_hand_rank))
            eval.description = f"{high_card} high"
        
        # Draw description
        draw_parts = []
        
        if eval.is_combo_draw:
            draw_parts.append("COMBO DRAW (Flush + Straight)")
        else:
            if eval.has_flush_draw:
                draw_parts.append(f"Flush Draw ({eval.flush_draw_outs} outs)")
            elif eval.has_backdoor_flush_draw:
                draw_parts.append("Backdoor Flush Draw")
            
            if eval.has_oesd:
                draw_parts.append(f"Open-Ended Straight Draw ({eval.straight_draw_outs} outs)")
            elif eval.has_gutshot:
                draw_parts.append(f"Gutshot Straight Draw ({eval.straight_draw_outs} outs)")
            elif eval.has_backdoor_straight_draw:
                draw_parts.append("Backdoor Straight Draw")
        
        if not draw_parts:
            # Check for no draw possibilities
            hero_suits = [c.suit for c in hero]
            board_suits = [c.suit for c in board]
            
            # Check if hero has any suit connection
            hero_suit_connections = [suit for suit in hero_suits if suit in board_suits]
            
            if not hero_suit_connections:
                draw_parts.append("No flush possibilities")
            
            draw_parts.append("No straight draws")
        
        eval.draw_description = " • ".join(draw_parts)


# Singleton instance
_evaluator = HandEvaluator()


def evaluate_hand(hero_cards: List[str], board_cards: List[str]) -> HandEvaluation:
    """Convenience function for hand evaluation"""
    return _evaluator.evaluate_hand(hero_cards, board_cards)
