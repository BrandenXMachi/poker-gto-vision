"""
Poker UI detection using YOLOv8 and OCR
Detects hero turn, buttons, cards, pot size, and other poker elements
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("YOLOv8 not available, using fallback detection")

from .ocr import OCRProcessor

logger = logging.getLogger(__name__)


class PokerDetector:
    """Main detector class for poker UI elements"""
    
    def __init__(self):
        """Initialize detector with lightweight color-based detection (FAST MODE)"""
        # Skip OCR for performance - not needed for MVP
        self.ocr = None
        
        # Skip YOLO for performance - color detection is sufficient
        self.model = None
        
        logger.info("Initialized FAST MODE detector (color-based detection only)")
        
        # Detection thresholds
        self.button_confidence = 0.5
        self.card_confidence = 0.4
        
    def detect(self, frame: np.ndarray) -> Dict:
        """
        Main detection pipeline (FAST MODE - color-based only)
        Returns detected poker elements
        """
        detections = {
            "hero_turn": False,
            "buttons_visible": False,
            "timer_active": False,
            "cards": [],
            "pot_size": None,
            "stacks": {},
            "actions": [],
            "vpip_stats": {},
            "dealer_button_position": None,
            "hero_position": None  # Will be calculated from button position
        }
        
        try:
            # Lightweight preprocessing - just resize
            processed = self._preprocess_frame(frame)
            
            # Fast hero turn detection using color analysis only
            detections["hero_turn"] = self._detect_hero_turn(processed)
            detections["buttons_visible"] = detections["hero_turn"]  # Same detection
            detections["timer_active"] = False  # Skip expensive circle detection
            
            # Detect dealer button position for GGPoker 6-max
            button_seat = self._detect_dealer_button(processed)
            if button_seat:
                detections["dealer_button_position"] = button_seat
                # Calculate hero position (hero is always bottom-center in GGPoker)
                detections["hero_position"] = self._calculate_hero_position(button_seat)
                logger.info(f"Button at seat {button_seat}, Hero position: {detections['hero_position']}")
            
            # Skip YOLO - not needed for MVP
            # Skip OCR - not needed for MVP
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        return detections
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        FAST preprocessing - just resize to smaller dimensions
        """
        # Aggressive resize for maximum speed
        height, width = frame.shape[:2]
        max_dim = 640  # Reduced from 1280 for faster processing
        
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # Skip CLAHE - too slow, not essential for color detection
        return frame
    
    def _detect_hero_turn(self, frame: np.ndarray) -> bool:
        """
        Detect if it's hero's turn using multiple signals:
        - Action buttons visible (FOLD, CALL, RAISE)
        - Timer circle active
        - Seat highlight/glow
        """
        # Look for bright green/yellow colors (common for action buttons)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Green button detection (CALL/CHECK buttons are often green)
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Yellow/orange detection (timer, highlights)
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Red button detection (FOLD button)
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        
        # Count pixels for each color
        green_pixels = cv2.countNonZero(green_mask)
        yellow_pixels = cv2.countNonZero(yellow_mask)
        red_pixels = cv2.countNonZero(red_mask)
        
        # Hero turn likely if we see multiple button colors
        button_threshold = 500  # Minimum pixels for detection
        buttons_detected = sum([
            green_pixels > button_threshold,
            yellow_pixels > button_threshold,
            red_pixels > button_threshold
        ])
        
        return buttons_detected >= 2
    
    def _detect_buttons(self, frame: np.ndarray) -> bool:
        """Detect if action buttons (FOLD, CALL, RAISE) are visible"""
        # Use template matching or color detection
        # For MVP, we use color detection from _detect_hero_turn
        return self._detect_hero_turn(frame)
    
    def _detect_timer(self, frame: np.ndarray) -> bool:
        """Detect if timer circle is active"""
        # Look for circular shapes with specific colors
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100
        )
        
        return circles is not None and len(circles[0]) > 0
    
    def _detect_dealer_button(self, frame: np.ndarray) -> Optional[int]:
        """
        Detect dealer button "D" marker in GGPoker 6-max layout
        
        Returns seat number (1-6) where button is located:
        - Seat 1: Bottom-left
        - Seat 2: Top-left  
        - Seat 3: Top-center
        - Seat 4: Top-right
        - Seat 5: Bottom-right
        - Seat 6: Bottom-center (Hero)
        """
        height, width = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # MORE SENSITIVE: Wider yellow detection range
        # Expanded HSV range to catch dealer button in various lighting
        lower_yellow = np.array([15, 100, 100])  # Wider hue, lower saturation/value
        upper_yellow = np.array([35, 255, 255])  # Wider hue range
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Also detect orange-yellow (some tables use orange button)
        lower_orange = np.array([10, 100, 100])
        upper_orange = np.array([20, 255, 255])
        orange_mask = cv2.inRange(hsv, lower_orange, upper_orange)
        
        # Combine yellow and orange masks
        combined_mask = cv2.bitwise_or(yellow_mask, orange_mask)
        
        # Define regions for 6 seats in GGPoker layout
        # Each region is (y_start, y_end, x_start, x_end) as percentages
        seat_regions = {
            1: (0.50, 0.80, 0.05, 0.25),  # Bottom-left
            2: (0.15, 0.40, 0.05, 0.25),  # Top-left
            3: (0.10, 0.35, 0.35, 0.65),  # Top-center
            4: (0.15, 0.40, 0.75, 0.95),  # Top-right
            5: (0.50, 0.80, 0.75, 0.95),  # Bottom-right
            6: (0.60, 0.90, 0.35, 0.65),  # Bottom-center (Hero)
        }
        
        # Check each region for yellow/orange "D" marker
        max_yellow_pixels = 0
        button_seat = None
        
        for seat, (y1_pct, y2_pct, x1_pct, x2_pct) in seat_regions.items():
            y1 = int(height * y1_pct)
            y2 = int(height * y2_pct)
            x1 = int(width * x1_pct)
            x2 = int(width * x2_pct)
            
            region = combined_mask[y1:y2, x1:x2]
            yellow_pixels = cv2.countNonZero(region)
            
            # Lower threshold for more sensitive detection
            if yellow_pixels > max_yellow_pixels and yellow_pixels > 20:  # Was 50, now 20
                max_yellow_pixels = yellow_pixels
                button_seat = seat
                logger.info(f"Button candidate at seat {seat}: {yellow_pixels} yellow pixels")
        
        if button_seat:
            logger.info(f"✓ Dealer button detected at seat {button_seat}")
        else:
            logger.warning("⚠ No dealer button detected in frame")
        
        return button_seat
    
    def _calculate_hero_position(self, button_seat: int) -> str:
        """
        Calculate hero's position based on dealer button location
        Hero is always at seat 6 (bottom-center) in GGPoker
        
        Args:
            button_seat: Seat number where dealer button is (1-6)
            
        Returns:
            Position name: 'UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'
        """
        # Hero is always seat 6 in GGPoker
        hero_seat = 6
        
        # Calculate seats between button and hero (clockwise)
        seats_after_button = (hero_seat - button_seat) % 6
        
        # Map to position names (6-max)
        position_map = {
            0: "BTN",    # Hero is the button
            1: "SB",     # 1 seat after button = Small Blind
            2: "BB",     # 2 seats after button = Big Blind
            3: "UTG",    # 3 seats after button = Under The Gun
            4: "MP",     # 4 seats after button = Middle Position
            5: "CO",     # 5 seats after button = Cutoff
        }
        
        position = position_map.get(seats_after_button, "unknown")
        return position
    
    def _yolo_detect(self, frame: np.ndarray) -> Dict:
        """Use YOLO for object detection (cards, seats, etc.)"""
        results = {}
        
        try:
            if self.model:
                predictions = self.model(frame, verbose=False)
                
                # Parse YOLO results
                # Note: Custom model would be trained on poker-specific classes
                # For now, this is a placeholder structure
                results["cards"] = []
                results["seats"] = []
                
        except Exception as e:
            logger.error(f"YOLO detection error: {e}")
        
        return results
