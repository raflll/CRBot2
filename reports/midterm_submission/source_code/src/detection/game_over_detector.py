"""Game over detection using OCR for Clash Royale Merge Tactics."""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)

@dataclass
class GameOverDetection:
    """Result of game over detection."""
    is_game_over: bool = False
    has_quit_button: bool = False
    quit_button_location: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    has_play_again_button: bool = False
    play_again_button_location: Optional[Tuple[int, int, int, int]] = None
    game_result: Optional[str] = None  # "victory" or "defeat"
    confidence: float = 0.0

class GameOverDetector:
    """Detects game over state and UI elements using OCR."""
    
    def __init__(self):
        """Initialize the game over detector."""
        self.ocr_reader = None
        self._init_ocr()
        
    def _init_ocr(self):
        """Initialize OCR reader."""
        try:
            import easyocr
            import torch
            
            # Check for available acceleration
            use_gpu = False
            device_info = "CPU"
            
            if torch.cuda.is_available():
                use_gpu = True
                device_info = "CUDA GPU"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # MPS (Metal Performance Shaders) for Mac
                # Note: EasyOCR may not fully support MPS yet, but we can try
                use_gpu = True
                device_info = "Apple Metal GPU (MPS)"
            
            try:
                self.ocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
                logger.info(f"OCR reader initialized with {device_info}")
            except Exception as e:
                # Fallback to CPU if GPU initialization fails
                logger.warning(f"Failed to initialize with {device_info}: {e}")
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                logger.info("OCR reader initialized with CPU (fallback)")
                
        except ImportError:
            logger.warning("EasyOCR not installed. Install with: pip install easyocr")
        except Exception as e:
            logger.error(f"Failed to initialize OCR: {e}")
    
    def detect(self, screenshot: np.ndarray) -> GameOverDetection:
        """
        Detect game over state and UI elements.
        
        Args:
            screenshot: Screenshot as numpy array (BGR format)
            
        Returns:
            GameOverDetection object with detection results
        """
        result = GameOverDetection()
        
        if self.ocr_reader is None:
            logger.warning("OCR reader not available")
            return result
        
        try:
            # Convert BGR to RGB for OCR
            if len(screenshot.shape) == 3 and screenshot.shape[2] == 3:
                rgb_image = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = screenshot
            
            # Run OCR on the screenshot
            ocr_results = self.ocr_reader.readtext(rgb_image)
            
            # Process OCR results
            for (bbox, text, confidence) in ocr_results:
                text_lower = text.lower().strip()
                
                # Check for "Quit" button
                if text_lower == "quit" and confidence > 0.7:
                    result.has_quit_button = True
                    result.quit_button_location = self._bbox_to_rect(bbox)
                    result.is_game_over = True
                    result.confidence = max(result.confidence, confidence)
                    logger.info(f"Detected 'Quit' button at {result.quit_button_location} with confidence {confidence:.2f}")
                
                # Check for "Play Again" button
                elif "play" in text_lower and "again" in text_lower and confidence > 0.7:
                    result.has_play_again_button = True
                    result.play_again_button_location = self._bbox_to_rect(bbox)
                    result.is_game_over = True
                    result.confidence = max(result.confidence, confidence)
                    logger.info(f"Detected 'Play Again' button at {result.play_again_button_location} with confidence {confidence:.2f}")
                
                # Check for victory/defeat text
                elif "defeated" in text_lower and confidence > 0.6:
                    result.game_result = "defeat"
                    result.is_game_over = True
                    logger.info(f"Detected 'Defeated' text with confidence {confidence:.2f}")
                
                # Check for victory indicators (could be "Victory", "Winner", etc.)
                elif any(word in text_lower for word in ["victory", "winner", "won"]) and confidence > 0.6:
                    result.game_result = "victory"
                    result.is_game_over = True
                    logger.info(f"Detected victory indicator: '{text}' with confidence {confidence:.2f}")
                
                # Check for rank indicators (e.g., "4" with wreath)
                elif text_lower.isdigit() and confidence > 0.8:
                    # Check if this is near a wreath/laurel (game over screen indicator)
                    # This is a supplementary check
                    y_coord = bbox[0][1]
                    if y_coord < screenshot.shape[0] * 0.5:  # Upper half of screen
                        result.is_game_over = True
                        logger.debug(f"Detected rank number '{text}' as potential game over indicator")
            
            if result.is_game_over:
                logger.info(f"Game over detected - Quit button: {result.has_quit_button}, Play Again: {result.has_play_again_button}")
            
        except Exception as e:
            logger.error(f"Error during game over detection: {e}")
        
        return result
    
    def _bbox_to_rect(self, bbox) -> Tuple[int, int, int, int]:
        """
        Convert OCR bounding box to rectangle coordinates.
        
        Args:
            bbox: Bounding box from OCR [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            
        Returns:
            Tuple of (x, y, width, height)
        """
        points = np.array(bbox, dtype=np.int32)
        x = np.min(points[:, 0])
        y = np.min(points[:, 1])
        width = np.max(points[:, 0]) - x
        height = np.max(points[:, 1]) - y
        return (int(x), int(y), int(width), int(height))
    
    def get_button_center(self, button_location: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Get the center point of a button for clicking.
        
        Args:
            button_location: Button location as (x, y, width, height)
            
        Returns:
            Tuple of (center_x, center_y)
        """
        if button_location:
            x, y, width, height = button_location
            return (x + width // 2, y + height // 2)
        return None
    
    def detect_quick(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """
        Quick detection method for integration with existing systems.
        
        Args:
            screenshot: Screenshot as numpy array
            
        Returns:
            Dictionary with detection results
        """
        detection = self.detect(screenshot)
        return {
            'is_game_over': detection.is_game_over,
            'has_quit_button': detection.has_quit_button,
            'quit_button_center': self.get_button_center(detection.quit_button_location) if detection.quit_button_location else None,
            'has_play_again_button': detection.has_play_again_button,
            'play_again_button_center': self.get_button_center(detection.play_again_button_location) if detection.play_again_button_location else None,
            'game_result': detection.game_result,
            'confidence': detection.confidence
        }