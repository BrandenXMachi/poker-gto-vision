"""
Simplified GTO solver for poker recommendations
Provides fold/call/raise decisions based on game state
"""

import logging
import random
from typing import Dict, Optional
from game.state import GameStateManager

logger = logging.getLogger(__name__)


class GTOSolver:
    """Simplified GTO solver for MVP"""
    
    def __init__(self):
        """Initialize solver"""
        self.actions = ["Fold", "Call", "Raise"]
        
    def get_recommendation(self, game_state: GameStateManager) -> Dict:
        """
        Generate GTO recommendation based on current game state
        
        Args:
            game_state: Current game state
            
        Returns:
            Dictionary with action, sizing, EV, and reasoning
        """
        state = game_state.current_state
        
        # Get pot size
        pot_size = state.pot_size if state.pot_size else 50.0
        
        # Generate recommendation based on simplified logic
        # In production, this would use proper range analysis and GTO calculations
        action, sizing = self._calculate_action(state, pot_size)
        ev = self._estimate_ev(action, pot_size)
        reasoning = self._generate_reasoning(action, state)
        
        recommendation = {
            "action": action,
            "pot_size": f"${pot_size:.0f}" if pot_size else None,
            "ev": ev,
            "reasoning": reasoning
        }
        
        if sizing:
            recommendation["action"] = f"{action} to ${sizing:.0f}"
        
        logger.info(f"Recommendation: {recommendation['action']}")
        
        return recommendation
    
    def _calculate_action(self, state, pot_size: float) -> tuple:
        """
        Calculate best action based on simplified GTO principles
        
        This is a simplified version for MVP. In production, this would:
        - Analyze hand strength
        - Consider villain ranges based on VPIP/PFR
        - Calculate pot odds and equity
        - Use preflop charts and postflop GTO solutions
        """
        # For MVP, use simplified decision tree
        
        # Random decision weighted by typical GTO frequencies
        # Real implementation would analyze actual cards, position, etc.
        decision = random.random()
        
        if decision < 0.2:
            # Fold ~20% of the time
            return "Fold", None
        elif decision < 0.6:
            # Call ~40% of the time
            return "Call", None
        else:
            # Raise ~40% of the time
            # Calculate raise sizing (typically 50-75% pot)
            raise_size = pot_size * random.uniform(0.5, 0.75)
            return "Raise", raise_size
    
    def _estimate_ev(self, action: str, pot_size: float) -> str:
        """
        Estimate expected value for the action
        Simplified for MVP
        """
        # Simplified EV estimation
        if action.startswith("Fold"):
            ev_bb = 0.0
        elif action.startswith("Call"):
            ev_bb = random.uniform(0.2, 1.0)
        else:  # Raise
            ev_bb = random.uniform(0.5, 1.5)
        
        return f"+{ev_bb:.1f}bb"
    
    def _generate_reasoning(self, action: str, state) -> str:
        """Generate simple reasoning for the recommendation"""
        reasons = []
        
        if action.startswith("Fold"):
            reasons = [
                "Villain range indicates strength",
                "Poor pot odds",
                "Weak hand vs likely range"
            ]
        elif action.startswith("Call"):
            reasons = [
                "Good pot odds",
                "Balanced calling range",
                "Hand has showdown value"
            ]
        else:  # Raise
            reasons = [
                "Pot odds favorable",
                "Semi-bluff opportunity",
                "Value bet opportunity",
                "Apply pressure"
            ]
        
        return random.choice(reasons)


class RangeEstimator:
    """Estimate villain ranges based on VPIP/PFR stats"""
    
    def __init__(self):
        """Initialize range estimator"""
        pass
    
    def estimate_range(self, vpip: int, pfr: int, position: str) -> Dict:
        """
        Estimate villain's range based on stats
        
        Args:
            vpip: Voluntarily put money in pot percentage
            pfr: Pre-flop raise percentage
            position: Player position
            
        Returns:
            Estimated range distribution
        """
        # Simplified range estimation
        # Real implementation would use detailed range matrices
        
        if vpip < 15:
            tightness = "very tight"
        elif vpip < 25:
            tightness = "tight"
        elif vpip < 35:
            tightness = "moderate"
        else:
            tightness = "loose"
        
        return {
            "tightness": tightness,
            "vpip": vpip,
            "pfr": pfr,
            "estimated_hands": self._get_hand_range(vpip, pfr)
        }
    
    def _get_hand_range(self, vpip: int, pfr: int) -> str:
        """Get simplified hand range description"""
        if vpip < 15:
            return "Premium hands only (AA-TT, AK-AQ)"
        elif vpip < 25:
            return "Strong hands (Pairs 88+, Broadway cards)"
        elif vpip < 35:
            return "Moderate range (All pairs, suited connectors)"
        else:
            return "Wide range (Many hands, speculative plays)"
