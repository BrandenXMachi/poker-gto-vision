"""
Pure GTO solver for poker recommendations
Uses pot odds, position, and fundamental poker principles
No exploitative play based on opponent stats
"""

import logging
from typing import Dict, Optional, Tuple
from game.state import GameStateManager

logger = logging.getLogger(__name__)


class GTOSolver:
    """
    Pure GTO solver based on fundamental poker math
    
    Strategy focuses on:
    - Pot odds calculations
    - Position-based play (when available)
    - Number of opponents in the hand
    - Stack depth relative to pot
    - GTO balanced frequencies
    
    Does NOT use:
    - Opponent HUD stats (VPIP/PFR)
    - Exploitative adjustments
    - Player profiling
    """
    
    def __init__(self):
        """Initialize solver with GTO parameters"""
        self.actions = ["Fold", "Call", "Raise"]
        
        # GTO balanced frequencies (without card information)
        # These are defensive defaults when we can't see hero's cards
        self.gto_frequencies = {
            "early_position": {"fold": 0.60, "call": 0.25, "raise": 0.15},
            "middle_position": {"fold": 0.50, "call": 0.30, "raise": 0.20},
            "late_position": {"fold": 0.35, "call": 0.35, "raise": 0.30},
            "button": {"fold": 0.25, "call": 0.35, "raise": 0.40},
            "unknown": {"fold": 0.45, "call": 0.35, "raise": 0.20},
        }
        
    def get_recommendation(self, game_state: GameStateManager) -> Dict:
        """
        Generate GTO recommendation based on game state fundamentals
        
        Args:
            game_state: Current game state with pot, position, etc.
            
        Returns:
            Dictionary with action, sizing in BB, EV, and reasoning
        """
        state = game_state.current_state
        
        # Extract fundamental game information
        pot_dollars = state.pot_size if state.pot_size else 50.0
        
        # Determine big blind size (detect or assume standard)
        big_blind = self._detect_big_blind(state)
        
        # Convert pot to BB
        pot_bb = pot_dollars / big_blind
        
        # Detect position (if available)
        position = self._detect_position(state)
        
        # Count active players (if available)
        num_players = self._count_players(state)
        
        # Calculate action based on GTO fundamentals
        action, sizing_bb = self._calculate_gto_action(
            pot_bb=pot_bb,
            position=position,
            num_players=num_players
        )
        
        # Estimate EV based on GTO principles
        ev = self._estimate_gto_ev(action, pot_bb, position)
        
        # Generate reasoning based on fundamentals
        reasoning = self._generate_gto_reasoning(action, pot_bb, position, num_players)
        
        recommendation = {
            "action": action,
            "pot_size": f"{pot_bb:.1f} BB",
            "ev": ev,
            "reasoning": reasoning
        }
        
        if sizing_bb:
            recommendation["action"] = f"{action} {sizing_bb:.0f} BB"
        
        logger.info(f"GTO Recommendation: {recommendation['action']} | Position: {position} | Pot: {pot_bb:.1f} BB")
        
        return recommendation
    
    def _detect_big_blind(self, state) -> float:
        """
        Detect or infer big blind size from game state
        
        Returns: Big blind size in dollars (default $2 for typical online game)
        """
        # TODO: Implement BB detection from OCR/computer vision
        # For now, use common online stakes
        # Could detect from:
        # - Blinds posted in action history
        # - Stake level indicators on table
        # - Pattern recognition from typical pot sizes
        
        # Default to $2 BB (common $1/$2 NLHE game)
        return 2.0
    
    def _detect_position(self, state) -> str:
        """
        Detect hero's position at the table
        
        Returns: 'early_position', 'middle_position', 'late_position', 'button', or 'unknown'
        """
        # TODO: Implement position detection from computer vision
        # For now, return unknown
        # Future: detect based on seat position, dealer button location
        return "unknown"
    
    def _count_players(self, state) -> int:
        """
        Count number of active players in the hand
        
        Returns: Number of players (default 6 for full ring)
        """
        if state.players:
            return len(state.players)
        # Default assumption: 6-max table
        return 6
    
    def _calculate_gto_action(
        self,
        pot_bb: float,
        position: str,
        num_players: int
    ) -> Tuple[str, Optional[float]]:
        """
        Calculate GTO action based on fundamentals
        
        Args:
            pot_bb: Pot size in big blinds
            position: Hero's position
            num_players: Number of active players
        
        Returns:
            Tuple of (action, sizing_in_bb)
        
        Strategy without hand information:
        1. Use position to determine baseline strategy
        2. Adjust for pot size (pot odds)
        3. Consider number of opponents
        4. Default to GTO balanced frequencies
        
        Pure GTO approach: We balance our range to remain unexploitable
        """
        
        # Get GTO frequencies for position
        frequencies = self.gto_frequencies.get(position, self.gto_frequencies["unknown"])
        
        # Adjust for number of players
        # More players = tighter (less equity against multiple opponents)
        if num_players >= 8:
            # Full ring: play tighter
            frequencies = self._tighten_range(frequencies, 0.15)
        elif num_players <= 4:
            # Short-handed: play looser
            frequencies = self._loosen_range(frequencies, 0.15)
        
        # Adjust for pot size (pot odds in BB)
        # Larger pot = more incentive to continue
        pot_odds_factor = self._calculate_pot_odds_factor(pot_bb)
        
        if pot_odds_factor > 1.5:
            # Large pot: reduce folding frequency
            frequencies["fold"] = max(frequencies["fold"] - 0.15, 0.20)
            frequencies["call"] = frequencies["call"] + 0.10
            frequencies["raise"] = frequencies["raise"] + 0.05
        elif pot_odds_factor < 0.5:
            # Small pot: more flexible to fold
            frequencies["fold"] = min(frequencies["fold"] + 0.10, 0.70)
            frequencies["call"] = max(frequencies["call"] - 0.05, 0.15)
            frequencies["raise"] = max(frequencies["raise"] - 0.05, 0.10)
        
        # Make decision based on GTO frequencies
        # Use pot size with proper hash distribution for consistency
        import hashlib
        
        # Create deterministic but well-distributed hash
        seed_string = f"{pot_bb:.2f}_{position}_{num_players}"
        hash_value = int(hashlib.md5(seed_string.encode()).hexdigest(), 16)
        decision_value = (hash_value % 10000) / 10000.0  # Better distribution 0.0000-0.9999
        
        logger.info(f"Decision calc: pot_bb={pot_bb:.2f}, seed={seed_string}, decision_value={decision_value:.4f}, fold_threshold={frequencies['fold']:.2f}")
        
        # Apply frequency thresholds
        if decision_value < frequencies["fold"]:
            return "Fold", None
        elif decision_value < (frequencies["fold"] + frequencies["call"]):
            return "Call", None
        else:
            # Raise with GTO sizing in BB
            raise_size_bb = self._calculate_gto_sizing(pot_bb)
            return "Raise", raise_size_bb
    
    def _tighten_range(self, frequencies: Dict, adjustment: float) -> Dict:
        """Tighten range by increasing fold frequency"""
        return {
            "fold": min(frequencies["fold"] + adjustment, 0.75),
            "call": frequencies["call"],
            "raise": max(frequencies["raise"] - adjustment, 0.10)
        }
    
    def _loosen_range(self, frequencies: Dict, adjustment: float) -> Dict:
        """Loosen range by decreasing fold frequency"""
        return {
            "fold": max(frequencies["fold"] - adjustment, 0.20),
            "call": frequencies["call"],
            "raise": min(frequencies["raise"] + adjustment, 0.45)
        }
    
    def _calculate_pot_odds_factor(self, pot_size: float) -> float:
        """
        Calculate pot odds factor (normalized pot size)
        
        Returns: Factor indicating pot size relative to typical bet
        """
        # Typical bet is around $50-100
        # Factor > 1 = large pot, Factor < 1 = small pot
        return pot_size / 75.0
    
    def _calculate_gto_sizing(self, pot_size: float) -> float:
        """
        Calculate GTO raise sizing
        
        GTO principle: Bet between 50-75% of pot for balance
        - Too small: opponents get good odds to call
        - Too large: opponents easily fold marginal hands
        
        Standard GTO: 66% pot (2/3 pot)
        """
        # 66% pot sizing (GTO standard)
        return pot_size * 0.66
    
    def _estimate_gto_ev(self, action: str, pot_size: float, position: str) -> str:
        """
        Estimate EV based on GTO principles
        
        EV without hand knowledge:
        - Position improves EV
        - Larger pots increase call/raise EV
        - Folding always 0 EV
        """
        if action.startswith("Fold"):
            # Folding has 0 EV
            return "0.0bb"
            
        # Base EV adjustments by position
        position_ev_bonus = {
            "button": 0.3,
            "late_position": 0.2,
            "middle_position": 0.0,
            "early_position": -0.2,
            "unknown": 0.0
        }
        
        position_bonus = position_ev_bonus.get(position, 0.0)
        
        if action.startswith("Call"):
            # Call EV depends on pot odds and position
            base_ev = 0.2
            pot_factor = min(pot_size / 100.0, 1.0) * 0.3
            ev_bb = base_ev + position_bonus + pot_factor
            
        else:  # Raise
            # Raise EV from fold equity and position
            base_ev = 0.5
            ev_bb = base_ev + position_bonus
        
        return f"{ev_bb:+.1f}bb"
    
    def _generate_gto_reasoning(
        self,
        action: str,
        pot_bb: float,
        position: str,
        num_players: int
    ) -> str:
        """Generate reasoning based on GTO fundamentals (in BB)"""
        
        if action.startswith("Fold"):
            if num_players >= 8:
                return f"Full ring ({num_players}p) - tight GTO fold"
            elif pot_bb < 20:
                return f"Small pot ({pot_bb:.1f} BB) - no pot odds to continue"
            else:
                return "GTO balanced fold to remain unexploitable"
                
        elif action.startswith("Call"):
            if pot_bb > 50:
                return f"Large pot ({pot_bb:.1f} BB) - good pot odds to call"
            elif position in ["button", "late_position"]:
                return f"{position.replace('_', ' ').title()} - positional call"
            elif num_players <= 4:
                return f"Short-handed ({num_players}p) - wider calling range"
            else:
                return "GTO balanced call with implied odds"
                
        else:  # Raise
            if position in ["button", "late_position"]:
                return f"{position.replace('_', ' ').title()} - aggressive GTO raise"
            elif pot_bb < 25:
                return f"Small pot ({pot_bb:.1f} BB) - raise to build pot"
            elif num_players <= 4:
                return f"Short-handed ({num_players}p) - aggressive raise"
            else:
                return "GTO standard raise (66% pot) for balance"


class RangeEstimator:
    """
    Range estimator based on position and pot odds
    (No longer uses VPIP/PFR stats)
    """
    
    def __init__(self):
        """Initialize range estimator"""
        pass
    
    def estimate_range_by_position(self, position: str, num_players: int = 6) -> Dict:
        """
        Estimate GTO range based on position
        
        Args:
            position: Player position
            num_players: Number of players at table
            
        Returns:
            Estimated range distribution
        """
        if position == "button":
            range_pct = 45
            description = "Wide: Top 45% of hands"
        elif position == "late_position":
            range_pct = 30
            description = "Moderate-wide: Top 30%"
        elif position == "middle_position":
            range_pct = 20
            description = "Tight-moderate: Top 20%"
        elif position == "early_position":
            range_pct = 12
            description = "Tight: Top 12% (premium hands)"
        else:
            range_pct = 20
            description = "Standard: Top 20%"
        
        # Adjust for table size
        if num_players >= 8:
            range_pct = int(range_pct * 0.8)  # Tighter in full ring
            description = f"Full ring adjusted - {description}"
        elif num_players <= 4:
            range_pct = int(range_pct * 1.2)  # Looser in short-handed
            description = f"Short-handed adjusted - {description}"
        
        return {
            "position": position,
            "range_percentage": range_pct,
            "description": description,
            "num_players": num_players,
            "strategy": "GTO balanced range"
        }
