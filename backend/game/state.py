"""
Game state management
Tracks current game state across frames
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """State for a single player"""
    position: str
    stack: Optional[float] = None
    vpip: Optional[int] = None
    pfr: Optional[int] = None
    last_action: Optional[str] = None
    is_hero: bool = False


@dataclass
class GameState:
    """Overall game state"""
    street: str = "preflop"  # preflop, flop, turn, river
    pot_size: Optional[float] = None
    board_cards: List[str] = field(default_factory=list)
    hero_cards: List[str] = field(default_factory=list)
    players: Dict[str, PlayerState] = field(default_factory=dict)
    action_sequence: List[str] = field(default_factory=list)
    hero_turn_active: bool = False
    last_hero_turn_time: Optional[datetime] = None


class GameStateManager:
    """Manages game state across frames"""
    
    def __init__(self):
        """Initialize game state manager"""
        self.current_state = GameState()
        self.previous_detections = {}
        self.hero_turn_cooldown = 5  # seconds between hero turn detections
        
    def update(self, detections: Dict):
        """Update game state based on new detections"""
        try:
            # Update pot size
            if detections.get("pot_size"):
                self.current_state.pot_size = self._parse_amount(detections["pot_size"])
            
            # Update VPIP stats
            if detections.get("vpip_stats"):
                self._update_vpip_stats(detections["vpip_stats"])
            
            # Update hero turn status
            if detections.get("hero_turn"):
                self._set_hero_turn(True)
            else:
                # Hero turn ended
                if self.current_state.hero_turn_active:
                    self.current_state.hero_turn_active = False
            
            # Store previous detections for comparison
            self.previous_detections = detections
            
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
    
    def is_hero_turn(self) -> bool:
        """Check if it's currently hero's turn"""
        # Check cooldown to avoid duplicate recommendations
        if self.current_state.last_hero_turn_time:
            elapsed = (datetime.now() - self.current_state.last_hero_turn_time).total_seconds()
            if elapsed < self.hero_turn_cooldown:
                return False
        
        return self.current_state.hero_turn_active
    
    def reset_hero_turn(self):
        """Reset hero turn flag after giving recommendation"""
        self.current_state.hero_turn_active = False
        self.current_state.last_hero_turn_time = datetime.now()
    
    def _set_hero_turn(self, active: bool):
        """Set hero turn state"""
        # Only set to active if not in cooldown
        if active:
            if self.current_state.last_hero_turn_time:
                elapsed = (datetime.now() - self.current_state.last_hero_turn_time).total_seconds()
                if elapsed < self.hero_turn_cooldown:
                    return
        
        self.current_state.hero_turn_active = active
    
    def _update_vpip_stats(self, stats: Dict):
        """Update VPIP/PFR stats for players"""
        # In a real implementation, this would associate stats with specific players
        # For MVP, we store generic stats
        if "vpip" in stats:
            logger.info(f"Detected VPIP: {stats['vpip']}%")
        if "pfr" in stats:
            logger.info(f"Detected PFR: {stats['pfr']}%")
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse currency string to float"""
        try:
            # Remove $ and other currency symbols
            clean = amount_str.replace("$", "").replace(",", "").strip()
            return float(clean)
        except (ValueError, AttributeError):
            return None
    
    def get_state_summary(self) -> Dict:
        """Get current state as dictionary"""
        return {
            "street": self.current_state.street,
            "pot_size": self.current_state.pot_size,
            "hero_turn": self.current_state.hero_turn_active,
            "board_cards": self.current_state.board_cards,
            "hero_cards": self.current_state.hero_cards,
            "action_sequence": self.current_state.action_sequence
        }
