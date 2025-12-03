#!/usr/bin/env python3
"""
Screenshot Collector for Merge Fight Tactics
Randomly captures screenshots at intervals for dataset creation
"""

import time
import random
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import sys

try:
    import mss
    import mss.tools
    import pytesseract
    import pyautogui
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Please run: pip install mss pillow pytesseract pyautogui opencv-python")
    print("Or use: ./run.sh to launch with automatic dependency installation")
    sys.exit(1)

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from src.bot.random_actions import RandomActionGenerator

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScreenshotCollector:
    """Collects screenshots for Merge Fight Tactics dataset"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the screenshot collector
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.session_id = self._generate_session_id()
        self.output_dir = Path(self.config['output_directory']) / self.session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.screenshot_count = 0
        self.metadata = []
        self.sct = mss.mss()
        self.stop_file = Path("STOP_SCREENSHOTS")
        self.running = True
        
        # Initialize random action generator
        self.random_action_generator = RandomActionGenerator()
        
        # Detect and log screen dimensions
        self.screen_dimensions = self._detect_screen_dimensions()
        self._adjust_capture_region()

        # Set up pyautogui safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Output directory: {self.output_dir}")
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "output_directory": "./screenshots",
            "capture_interval": {
                "min": 5.0,
                "max": 10.0
            },
            "session_duration": 300,  # 5 minutes default
            "capture_region": None,  # Full screen if None
            "monitor_index": 1,  # Primary monitor
            "image_format": "png",
            "metadata_save_interval": 10,  # Save metadata every 10 screenshots
            "randomize_intervals": True,
            "add_timestamp_overlay": False,
            "random_actions": {
                "enabled": False,
                "count": 3,
                "delay_between_actions": 1.0
            },
            "battle_button": {
                "wait_time": 5.0,
                "text": "Battle",
                "max_attempts": 3,
                "retry_delay": 2.0
            },
            "play_again_button": {
                "text": "Play Again",
                "wait_after_click": 3.0
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"Loaded config from {config_path}")
        
        return default_config
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = random.randint(1000, 9999)
        return f"session_{timestamp}_{random_suffix}"
    
    def _detect_screen_dimensions(self) -> Dict[str, Any]:
        """
        Detect screen dimensions for all available monitors
        
        Returns:
            Dictionary containing monitor information
        """
        dimensions = {
            "monitors": [],
            "all_monitors": None,
            "primary_monitor": None
        }
        
        # Get all monitor information
        for i, monitor in enumerate(self.sct.monitors):
            monitor_info = {
                "index": i,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"]
            }
            dimensions["monitors"].append(monitor_info)
            
            if i == 0:
                dimensions["all_monitors"] = monitor_info
            elif i == self.config['monitor_index']:
                dimensions["primary_monitor"] = monitor_info
        
        # Log detected dimensions
        logger.info(f"Detected {len(dimensions['monitors']) - 1} monitor(s)")
        for i, monitor in enumerate(dimensions["monitors"]):
            if i == 0:
                logger.info(f"All monitors combined: {monitor['width']}x{monitor['height']}")
            else:
                logger.info(f"Monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
        
        return dimensions
    
    def _adjust_capture_region(self):
        """
        Adjust capture region based on detected screen dimensions
        """
        # Get the selected monitor dimensions
        monitor_idx = min(self.config['monitor_index'], len(self.screen_dimensions['monitors']) - 1)
        monitor = self.screen_dimensions['monitors'][monitor_idx]
        
        # If auto_fullscreen is enabled or no capture region specified, use full monitor
        if self.config.get('auto_fullscreen', True) or not self.config['capture_region']:
            logger.info(f"Using full monitor {monitor_idx}: {monitor['width']}x{monitor['height']}")
            self.config['capture_region'] = None
            return
        
        # Check if configured region fits within monitor bounds
        configured_region = self.config['capture_region']
        max_x = configured_region['x'] + configured_region['width']
        max_y = configured_region['y'] + configured_region['height']
        
        # Adjust if region extends beyond monitor bounds
        if max_x > monitor['width'] or max_y > monitor['height']:
            logger.warning(f"Configured capture region ({configured_region['width']}x{configured_region['height']}) "
                         f"exceeds monitor bounds ({monitor['width']}x{monitor['height']})")
            
            # Use full monitor instead of cropping
            logger.info(f"Switching to full monitor capture: {monitor['width']}x{monitor['height']}")
            self.config['capture_region'] = None
        else:
            logger.info(f"Capture region fits within monitor bounds: "
                       f"{configured_region['width']}x{configured_region['height']} at "
                       f"({configured_region['x']}, {configured_region['y']})")
    
    def capture_screenshot(self) -> Dict[str, Any]:
        """
        Capture a single screenshot
        
        Returns:
            Dictionary with screenshot metadata
        """
        timestamp = datetime.now()
        filename = f"screenshot_{self.screenshot_count:06d}.{self.config['image_format']}"
        filepath = self.output_dir / filename
        
        # Determine capture region
        if self.config['capture_region']:
            monitor = {
                "left": self.config['capture_region']['x'],
                "top": self.config['capture_region']['y'],
                "width": self.config['capture_region']['width'],
                "height": self.config['capture_region']['height']
            }
        else:
            monitor = self.sct.monitors[self.config['monitor_index']]
        
        # Capture screenshot
        screenshot = self.sct.grab(monitor)
        
        # Convert to PIL Image for saving
        # MSS captures in BGRA format, need to convert to RGB
        img = Image.frombytes(
            'RGBA',  # First read as RGBA since MSS provides BGRA
            (screenshot.width, screenshot.height),
            screenshot.bgra,  # Use the BGRA data
            'raw',
            'BGRA'  # Specify that the raw data is in BGRA format
        )
        
        # Convert from RGBA to RGB (removes alpha channel)
        img = img.convert('RGB')
        
        # Save screenshot
        img.save(filepath, self.config['image_format'].upper())
        
        # Create metadata
        metadata = {
            "filename": filename,
            "filepath": str(filepath),
            "timestamp": timestamp.isoformat(),
            "screenshot_number": self.screenshot_count,
            "width": screenshot.width,
            "height": screenshot.height,
            "monitor_region": {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"]
            },
            "screen_dimensions": self.screen_dimensions
        }
        
        self.screenshot_count += 1
        self.metadata.append(metadata)
        
        # Log timing info if verbose
        if hasattr(self, 'last_capture_time'):
            actual_interval = timestamp.timestamp() - self.last_capture_time
            logger.info(f"Captured screenshot {self.screenshot_count}: {filename} (interval: {actual_interval:.1f}s)")
        else:
            logger.info(f"Captured screenshot {self.screenshot_count}: {filename}")
        
        self.last_capture_time = timestamp.timestamp()
        
        # Save metadata periodically
        if self.screenshot_count % self.config['metadata_save_interval'] == 0:
            self.save_metadata()
        
        return metadata
    
    def save_metadata(self):
        """Save metadata to JSON file"""
        metadata_path = self.output_dir / "metadata.json"
        
        session_metadata = {
            "session_id": self.session_id,
            "start_time": self.metadata[0]["timestamp"] if self.metadata else None,
            "last_update": datetime.now().isoformat(),
            "total_screenshots": self.screenshot_count,
            "config": self.config,
            "screenshots": self.metadata
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(session_metadata, f, indent=2)
        
        logger.debug(f"Saved metadata for {self.screenshot_count} screenshots")
    
    def find_and_click_play_again_button(self) -> bool:
        """
        Specialized detection for "Play Again" button which appears at bottom of screen.
        Looks for yellow button in the lower portion of the screen.

        Returns:
            True if Play Again button was found and clicked, False otherwise
        """
        try:
            logger.info("Looking for Play Again button using color detection...")

            # Capture screen
            monitor = self.sct.monitors[self.config['monitor_index']]
            screenshot = self.sct.grab(monitor)

            # Convert to numpy array
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

            # Only look at bottom 40% of screen where Play Again button appears
            height = img_bgr.shape[0]
            bottom_region = img_bgr[int(height * 0.6):, :]

            img_hsv = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2HSV)

            # Define color range for yellow/orange buttons
            lower_yellow = np.array([15, 100, 100])
            upper_yellow = np.array([35, 255, 255])

            # Create mask for yellow regions
            mask = cv2.inRange(img_hsv, lower_yellow, upper_yellow)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                logger.debug("No Play Again button found (no yellow regions in bottom area)")
                return False

            # Find the leftmost large button (Play Again is on the left)
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 5000:  # Button should be large
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        valid_contours.append((contour, cx, cy, area))

            if not valid_contours:
                logger.debug("No large yellow buttons found in bottom area")
                return False

            # Sort by x position (leftmost first) - Play Again is on the left
            valid_contours.sort(key=lambda x: x[1])
            leftmost = valid_contours[0]

            # Calculate absolute screen position
            center_x = leftmost[1] + monitor['left']
            center_y = leftmost[2] + int(height * 0.6) + monitor['top']

            logger.info(f"Found Play Again button at ({center_x}, {center_y})")
            pyautogui.click(center_x, center_y)
            logger.info("Clicked Play Again button")

            return True

        except Exception as e:
            logger.error(f"Error in Play Again detection: {e}")
            return False

    def find_and_click_button_simple(self, button_name: str) -> bool:
        """
        Simple button detection - just look for any yellow/orange button-like region
        and click it. This is a fallback when OCR doesn't work.

        Args:
            button_name: Name for logging purposes

        Returns:
            True if button area was found and clicked, False otherwise
        """
        try:
            logger.info(f"Looking for {button_name} button using color detection...")

            # Capture screen
            monitor = self.sct.monitors[self.config['monitor_index']]
            screenshot = self.sct.grab(monitor)

            # Convert to numpy array
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

            # Define color range for yellow/orange buttons (Battle button is yellow)
            # HSV ranges: Hue (0-180), Saturation (0-255), Value (0-255)
            lower_yellow = np.array([15, 100, 100])
            upper_yellow = np.array([35, 255, 255])

            # Create mask for yellow regions
            mask = cv2.inRange(img_hsv, lower_yellow, upper_yellow)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                logger.debug(f"No yellow regions found for {button_name}")
                return False

            # Find largest contour (likely the button)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)

            # Button should be reasonably large
            if area < 1000:
                logger.debug(f"Largest yellow region too small: {area} pixels")
                return False

            # Get center of the contour
            M = cv2.moments(largest_contour)
            if M["m00"] == 0:
                return False

            center_x = int(M["m10"] / M["m00"]) + monitor['left']
            center_y = int(M["m01"] / M["m00"]) + monitor['top']

            logger.info(f"Found {button_name} button at ({center_x}, {center_y})")
            pyautogui.click(center_x, center_y)
            logger.info(f"Clicked {button_name} button")

            return True

        except Exception as e:
            logger.error(f"Error in color detection for {button_name}: {e}")
            return False

    def find_and_click_text(self, target_text: str, confidence_threshold: float = 60.0) -> bool:
        """
        Find text on screen using OCR and click it

        Args:
            target_text: Text to search for (e.g., "Battle")
            confidence_threshold: Minimum confidence percentage (0-100)

        Returns:
            True if text was found and clicked, False otherwise
        """
        try:
            logger.info(f"Scanning screen for '{target_text}'...")

            # Capture current screen
            if self.config['capture_region']:
                monitor = {
                    "left": self.config['capture_region']['x'],
                    "top": self.config['capture_region']['y'],
                    "width": self.config['capture_region']['width'],
                    "height": self.config['capture_region']['height']
                }
            else:
                monitor = self.sct.monitors[self.config['monitor_index']]

            screenshot = self.sct.grab(monitor)
            logger.debug(f"Screenshot captured: {screenshot.width}x{screenshot.height}")

            # Convert to numpy array for OpenCV
            img_array = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

            # Run OCR with bounding box data
            logger.debug("Running OCR...")
            ocr_data = pytesseract.image_to_data(img_bgr, output_type=pytesseract.Output.DICT)
            logger.debug(f"OCR complete, found {len(ocr_data['text'])} text elements")

            # Log all detected text for debugging
            detected_texts = [t.strip() for t in ocr_data['text'] if t.strip()]
            if detected_texts:
                logger.debug(f"Detected text: {detected_texts}")

            # Search for the target text
            for i, text in enumerate(ocr_data['text']):
                if text.strip().lower() == target_text.lower():
                    confidence = float(ocr_data['conf'][i])

                    if confidence >= confidence_threshold:
                        # Get bounding box coordinates
                        x = ocr_data['left'][i]
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]

                        # Calculate center point
                        center_x = monitor['left'] + x + w // 2
                        center_y = monitor['top'] + y + h // 2

                        logger.info(f"Found '{target_text}' at ({center_x}, {center_y}) with {confidence:.1f}% confidence")

                        # Click the center of the text
                        pyautogui.click(center_x, center_y)
                        logger.info(f"Clicked '{target_text}' button")

                        return True

            logger.warning(f"Text '{target_text}' not found on screen")
            return False

        except Exception as e:
            logger.error(f"Error finding/clicking text '{target_text}': {e}")
            return False

    def check_stop_conditions(self) -> bool:
        """
        Check if collection should stop

        Returns:
            True if should stop, False otherwise
        """
        # Check for stop file
        if self.stop_file.exists():
            logger.info(f"Stop file detected: {self.stop_file}")
            self.stop_file.unlink()  # Remove the stop file
            return True

        return False
    
    def run_collection_session(self):
        """Run the main collection loop"""
        logger.info(f"Starting collection session for {self.config['session_duration']} seconds")
        logger.info("=" * 60)
        logger.info("TO STOP COLLECTION:")
        logger.info("  1. Press Ctrl+C")
        logger.info(f"  2. Create file: {self.stop_file}")
        logger.info("     Run: touch STOP_SCREENSHOTS")
        logger.info("=" * 60)

        # Try to click Battle button to start game
        battle_config = self.config.get('battle_button', {})
        wait_time = battle_config.get('wait_time', 5.0)
        button_text = battle_config.get('text', 'Battle')
        max_attempts = battle_config.get('max_attempts', 3)
        retry_delay = battle_config.get('retry_delay', 2.0)

        logger.info(f"Waiting {wait_time}s before looking for '{button_text}' button...")
        time.sleep(wait_time)

        # Try multiple times to find and click the button
        clicked = False
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Attempt {attempt}/{max_attempts}: Looking for '{button_text}' button...")

            # Try OCR first
            if self.find_and_click_text(button_text):
                clicked = True
                logger.info(f"Successfully clicked '{button_text}' button via OCR!")
                time.sleep(2.0)  # Wait for game to start
                break

            # Fallback to color detection
            if self.find_and_click_button_simple(button_text):
                clicked = True
                logger.info(f"Successfully clicked '{button_text}' button via color detection!")
                time.sleep(2.0)  # Wait for game to start
                break

            if attempt < max_attempts:
                logger.info(f"Button not found, retrying in {retry_delay}s...")
                time.sleep(retry_delay)

        if not clicked:
            logger.warning(f"Could not find '{button_text}' button after {max_attempts} attempts")
            logger.warning("Continuing with screenshot collection anyway...")

        start_time = time.time()
        
        try:
            while self.running and (time.time() - start_time < self.config['session_duration']):
                # Check stop conditions
                if self.check_stop_conditions():
                    logger.info("Stop condition detected")
                    break
                
                # Record time before actions
                action_start_time = time.time()

                # Capture screenshot
                self.capture_screenshot()

                # Check for "Play Again" button and click if found
                play_again_config = self.config.get('play_again_button', {})
                play_again_text = play_again_config.get('text', 'Play Again')

                # Try OCR first
                found_play_again = self.find_and_click_text(play_again_text, confidence_threshold=50.0)

                # Fallback to color detection if OCR fails
                if not found_play_again:
                    found_play_again = self.find_and_click_play_again_button()

                if found_play_again:
                    wait_time = play_again_config.get('wait_after_click', 3.0)
                    logger.info(f"Game ended - waiting {wait_time}s for new game to start...")
                    time.sleep(wait_time)

                # Perform random actions immediately after screenshot
                random_actions_config = self.config.get('random_actions', {})
                if random_actions_config.get('enabled', False):
                    try:
                        logger.info("Performing random actions after screenshot...")
                        performed_actions = self.random_action_generator.perform_action_sequence(random_actions_config)
                        if performed_actions:
                            logger.info(f"Completed {len(performed_actions)} random actions: {performed_actions}")
                    except Exception as e:
                        logger.error(f"Error performing random actions: {e}")
                
                # Calculate how much time has already passed
                action_duration = time.time() - action_start_time
                
                # Calculate next capture interval
                if self.config['randomize_intervals']:
                    desired_interval = random.uniform(
                        self.config['capture_interval']['min'],
                        self.config['capture_interval']['max']
                    )
                else:
                    desired_interval = self.config['capture_interval']['min']
                
                # Adjust sleep time to account for time already spent
                remaining_interval = max(0, desired_interval - action_duration)
                
                if remaining_interval > 0:
                    logger.debug(f"Waiting {remaining_interval:.1f}s (desired: {desired_interval:.1f}s, actions took: {action_duration:.1f}s)")
                    # Wait for next capture with interruptible sleep
                    sleep_start = time.time()
                    while time.time() - sleep_start < remaining_interval:
                        if self.check_stop_conditions():
                            self.running = False
                            break
                        time.sleep(0.5)  # Check every 0.5 seconds
                else:
                    logger.debug(f"Actions took {action_duration:.1f}s, exceeding interval of {desired_interval:.1f}s")
                
        except KeyboardInterrupt:
            logger.info("\nCollection stopped by user (Ctrl+C)")
        
        finally:
            # Save final metadata
            self.save_metadata()
            self._print_summary()
    
    def _print_summary(self):
        """Print collection session summary"""
        print("\n" + "="*50)
        print("SESSION SUMMARY")
        print("="*50)
        print(f"Session ID: {self.session_id}")
        print(f"Total screenshots: {self.screenshot_count}")
        print(f"Output directory: {self.output_dir}")
        print(f"Metadata saved: {self.output_dir / 'metadata.json'}")
        print("="*50)


def create_config_file():
    """Create a sample configuration file"""
    sample_config = {
        "output_directory": "./screenshots",
        "capture_interval": {
            "min": 1.0,
            "max": 3.0
        },
        "session_duration": 300,
        "auto_fullscreen": True,
        "capture_region": None,
        "monitor_index": 1,
        "image_format": "png",
        "metadata_save_interval": 10,
        "randomize_intervals": True,
        "add_timestamp_overlay": False,
        "random_actions": {
            "enabled": False,
            "count": 3,
            "delay_between_actions": 1.0
        }
    }
    
    config_path = Path("screenshot_config.json")
    
    if config_path.exists():
        print(f"Config file already exists at {config_path}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            return
    
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Created sample config file: {config_path}")
    print("Edit this file to customize capture settings")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Screenshot collector for Merge Fight Tactics dataset"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Collection duration in seconds (overrides config)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (overrides config)"
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a sample configuration file"
    )
    parser.add_argument(
        "--interval",
        type=float,
        help="Fixed capture interval in seconds"
    )
    parser.add_argument(
        "--interval-min",
        type=float,
        help="Minimum capture interval in seconds (for random intervals)"
    )
    parser.add_argument(
        "--interval-max", 
        type=float,
        help="Maximum capture interval in seconds (for random intervals)"
    )
    parser.add_argument(
        "--random-actions",
        type=int,
        metavar="COUNT",
        help="Enable random actions with specified count (overrides config)"
    )
    parser.add_argument(
        "--no-random-actions",
        action="store_true",
        help="Disable random actions (overrides config)"
    )

    args = parser.parse_args()
    
    if args.create_config:
        create_config_file()
        return
    
    # Initialize collector
    collector = ScreenshotCollector(args.config)
    
    # Override config with command line arguments
    if args.duration:
        collector.config['session_duration'] = args.duration
    
    if args.output:
        collector.config['output_directory'] = args.output
        collector.output_dir = Path(args.output) / collector.session_id
        collector.output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.interval:
        collector.config['capture_interval']['min'] = args.interval
        collector.config['capture_interval']['max'] = args.interval
        collector.config['randomize_intervals'] = False
    
    if args.interval_min:
        collector.config['capture_interval']['min'] = args.interval_min
        
    if args.interval_max:
        collector.config['capture_interval']['max'] = args.interval_max
    
    if args.no_random_actions:
        collector.config['random_actions']['enabled'] = False
    elif args.random_actions:
        collector.config['random_actions']['enabled'] = True
        collector.config['random_actions']['count'] = args.random_actions

    # Run collection
    print("\n" + "="*50)
    print("MERGE FIGHT TACTICS - SCREENSHOT COLLECTOR")
    print("="*50)
    print(f"Duration: {collector.config['session_duration']} seconds")
    print(f"Output: {collector.output_dir}")
    print(f"Interval: {collector.config['capture_interval']}")
    print("="*50)
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    collector.run_collection_session()


if __name__ == "__main__":
    main()