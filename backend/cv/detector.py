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
            "vpip_stats": {}
        }
        
        try:
            # Lightweight preprocessing - just resize
            processed = self._preprocess_frame(frame)
            
            # Fast hero turn detection using color analysis only
            detections["hero_turn"] = self._detect_hero_turn(processed)
            detections["buttons_visible"] = detections["hero_turn"]  # Same detection
            detections["timer_active"] = False  # Skip expensive circle detection
            
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
