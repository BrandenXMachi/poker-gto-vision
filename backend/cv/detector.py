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
        """Initialize detector with YOLO model and OCR"""
        self.ocr = OCRProcessor()
        
        # Initialize YOLO model (will use pre-trained or custom trained model)
        self.model = None
        if YOLO_AVAILABLE:
            try:
                # Try to load custom poker model, fallback to base YOLOv8
                model_path = Path(__file__).parent.parent / "models" / "poker_detector.pt"
                if model_path.exists():
                    self.model = YOLO(str(model_path))
                    logger.info("Loaded custom poker detection model")
                else:
                    # Use base YOLOv8 nano model for faster inference
                    self.model = YOLO('yolov8n.pt')
                    logger.info("Using base YOLOv8 model (train custom model for better results)")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
        
        # Detection thresholds
        self.button_confidence = 0.5
        self.card_confidence = 0.4
        
    def detect(self, frame: np.ndarray) -> Dict:
        """
        Main detection pipeline
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
            # Preprocess frame
            processed = self._preprocess_frame(frame)
            
            # Detect hero turn indicators
            detections["hero_turn"] = self._detect_hero_turn(processed)
            detections["buttons_visible"] = self._detect_buttons(processed)
            detections["timer_active"] = self._detect_timer(processed)
            
            # If YOLO model available, use it for object detection
            if self.model:
                yolo_results = self._yolo_detect(processed)
                detections.update(yolo_results)
            
            # OCR-based detections
            ocr_results = self.ocr.extract_text(processed)
            detections["pot_size"] = ocr_results.get("pot_size")
            detections["stacks"] = ocr_results.get("stacks", {})
            detections["vpip_stats"] = ocr_results.get("vpip_stats", {})
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        return detections
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for better detection
        - Resize if needed
        - Enhance contrast
        - Denoise if necessary
        """
        # Resize for faster processing (keep aspect ratio)
        height, width = frame.shape[:2]
        max_dim = 1280
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Apply CLAHE for better contrast (helps with glare)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
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
