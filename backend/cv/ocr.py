"""
OCR processing for poker text elements
Extracts pot size, stack sizes, VPIP/PFR stats, and other text
"""

import cv2
import numpy as np
import re
import logging
from typing import Dict, List, Optional

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logging.warning("EasyOCR not available")

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Handles all OCR operations for poker UI text"""
    
    def __init__(self):
        """Initialize OCR reader"""
        self.reader = None
        if EASYOCR_AVAILABLE:
            try:
                # Initialize EasyOCR with English language
                self.reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
    
    def extract_text(self, frame: np.ndarray) -> Dict:
        """
        Extract all text from frame and parse poker-specific information
        Returns pot size, stacks, VPIP stats, etc.
        """
        results = {
            "pot_size": None,
            "stacks": {},
            "vpip_stats": {},
            "raw_text": []
        }
        
        if not self.reader:
            return results
        
        try:
            # Run OCR on frame
            detections = self.reader.readtext(frame)
            
            # Parse detected text
            for (bbox, text, confidence) in detections:
                if confidence < 0.5:
                    continue
                
                results["raw_text"].append(text)
                
                # Parse pot size (look for $ or currency symbols)
                pot = self._parse_pot_size(text)
                if pot is not None:
                    results["pot_size"] = pot
                
                # Parse VPIP/PFR stats (look for percentages)
                vpip = self._parse_stats(text)
                if vpip:
                    results["vpip_stats"].update(vpip)
                
                # Parse stack sizes
                stack = self._parse_stack(text)
                if stack:
                    results["stacks"].update(stack)
        
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
        
        return results
    
    def _parse_pot_size(self, text: str) -> Optional[str]:
        """
        Extract pot size from text
        Looks for currency formats like: $45, 45.00, etc.
        """
        # Remove whitespace
        text = text.strip()
        
        # Look for currency patterns
        patterns = [
            r'\$\s*(\d+\.?\d*)',  # $45 or $45.00
            r'(\d+\.?\d*)\s*\$',  # 45$ or 45.00$
            r'Pot[\s:]*\$?\s*(\d+\.?\d*)',  # Pot: $45
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1)
                return f"${amount}"
        
        return None
    
    def _parse_stats(self, text: str) -> Dict:
        """
        Extract VPIP/PFR stats from text
        Looks for patterns like: VPIP: 25%, 25/15, etc.
        """
        stats = {}
        
        # Pattern for VPIP: XX%
        vpip_match = re.search(r'VPIP[\s:]*(\d+)%?', text, re.IGNORECASE)
        if vpip_match:
            stats["vpip"] = int(vpip_match.group(1))
        
        # Pattern for PFR: XX%
        pfr_match = re.search(r'PFR[\s:]*(\d+)%?', text, re.IGNORECASE)
        if pfr_match:
            stats["pfr"] = int(pfr_match.group(1))
        
        # Pattern for XX/YY format (VPIP/PFR)
        combined_match = re.search(r'(\d+)/(\d+)', text)
        if combined_match and not stats:
            stats["vpip"] = int(combined_match.group(1))
            stats["pfr"] = int(combined_match.group(2))
        
        return stats
    
    def _parse_stack(self, text: str) -> Dict:
        """
        Extract stack size from text
        """
        # Look for currency amounts that might be stack sizes
        match = re.search(r'\$\s*(\d+\.?\d*)', text)
        if match:
            amount = match.group(1)
            # Return with a generic key (in real implementation, 
            # would associate with player position)
            return {"stack": f"${amount}"}
        
        return {}
    
    def preprocess_for_ocr(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame specifically for better OCR results
        - Convert to grayscale
        - Apply thresholding
        - Enhance contrast
        """
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(binary)
        
        return denoised
