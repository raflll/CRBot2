#!/usr/bin/env python3
"""
Automated Data Collector for Game
Automatically plays the game and collects screenshots with actions
"""

import time
import random
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

try:
    import mss
    import mss.tools
    import pyautogui
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install mss pillow pyautogui")
    sys.exit(1)

from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from src.bot.random_actions import RandomActionGenerator
from src.detection.game_over_detector import GameOverDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomatedDataCollector:
    """Automated data collector that plays the game and captures screenshots"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the automated collector
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.session_id = self._generate_session_id()
        self.output_dir = Path(self.config['output_directory']) / self.session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.screenshot_count = 0
        self.game_count = 0
        self.metadata = []
        self.sct = mss.mss()
        self.stop_file = Path("STOP_AUTO_COLLECTOR")
        self.running = True
        
        # Game state tracking
        self.game_state = "menu"  # menu, playing, game_over
        self.last_action_time = time.time()
        self.game_start_time = None
        
        # Detect and log screen dimensions
        self.screen_dimensions = self._detect_screen_dimensions()
        self._adjust_capture_region()
        
        # Set up pyautogui safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Initialize random action generator
        self.random_action_generator = RandomActionGenerator()
        
        # Initialize game over detector
        self.game_over_detector = GameOverDetector()
        self.quit_clicked = False  # Track if we've clicked quit button
        
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Output directory: {self.output_dir}")
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "output_directory": "./screenshots",
            "capture_interval": {
                "min": 35.0,  # 30 seconds minimum between captures
                "max": 35.0   # 35 seconds maximum between captures
            },
            "session_duration": 3600,  # 60 minutes default
            "games_per_session": 1000,  # Maximum games to play (reduced default for testing)
            "capture_region": None,  # Full screen if None
            "monitor_index": 1,  # Primary monitor
            "image_format": "png",
            "metadata_save_interval": 10,
            "randomize_intervals": True,
            
            # Game-specific settings
            "game_window_title": None,  # Optional: specific window to focus
            "menu_start_key": "4",  # Key to press in menu to start
            "game_choices": ["1", "2", "3"],  # Random choices during game
            "choice_before_screenshot": True,
            "choice_delay": 5.0,  # Delay after making choice (increased to 2 seconds)
            
            # Click positions (will need to be configured)
            "play_again_position": {
                "x": 240,  # Center of screen typically
                "y": 600   # Adjust based on game
            },
            "play_again_detection_region": {
                "x": 200,
                "y": 550,
                "width": 80,
                "height": 100
            },
            
            # Timing settings
            "menu_wait_time": 5.0,  # Time to wait in menu before starting (increased from 2)
            "game_timeout": 300,  # Max time for a single game (5 minutes)
            "action_cooldown": 3.0,  # Minimum time between actions (increased from 0.5)
            
            # Detection thresholds
            "end_game_detection": {
                "enabled": True,
                "method": "ocr",  # "timeout", "pixel", "ocr"
                "timeout_seconds": 200,  # Fallback timeout if OCR fails
                "check_interval": 1.0
            },
            
            # Random actions configuration
            "random_actions": {
                "enabled": True,
                "count": 2,  # Number of random actions to perform
                "delay_between_actions": 1.0  # Delay between each action
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
        """Detect screen dimensions for all available monitors"""
        dimensions = {
            "monitors": [],
            "all_monitors": None,
            "primary_monitor": None
        }
        
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
        
        logger.info(f"Detected {len(dimensions['monitors']) - 1} monitor(s)")
        return dimensions
    
    def _adjust_capture_region(self):
        """Adjust capture region based on detected screen dimensions"""
        monitor_idx = min(self.config['monitor_index'], len(self.screen_dimensions['monitors']) - 1)
        monitor = self.screen_dimensions['monitors'][monitor_idx]
        
        if self.config.get('auto_fullscreen', True) or not self.config['capture_region']:
            logger.info(f"Using full monitor {monitor_idx}: {monitor['width']}x{monitor['height']}")
            self.config['capture_region'] = None
    
    def _press_key(self, key: str):
        """Press a keyboard key"""
        try:
            # Use pyautogui for keyboard input instead of keyboard library
            # as it's more compatible across platforms
            pyautogui.press(key)
            logger.info(f"Pressed key: {key}")
        except Exception as e:
            logger.error(f"Failed to press key {key}: {e}")
    
    def _make_random_choice(self):
        """Make a random choice from configured options"""
        if not self.config['choice_before_screenshot']:
            return None
        
        # Use the RandomActionGenerator for multiple actions
        random_actions_config = self.config.get('random_actions', {})
        if random_actions_config.get('enabled', False):
            logger.info("Performing multiple random actions...")
            performed_actions = self.random_action_generator.perform_action_sequence(random_actions_config)

            # Additional delay after all actions
            time.sleep(self.config['choice_delay'])
            return performed_actions
        else:
            # Fallback to single action
            choice = random.choice(self.config['game_choices'])
            self._press_key(choice)
            logger.info(f"Made random choice: {choice}")

            # Wait for the game to respond to the key press
            time.sleep(self.config['choice_delay'])
            return choice
    
    def _start_game_from_menu(self):
        """Start a new game from the menu"""
        logger.info("Starting new game from menu...")
        
        # Wait a moment to ensure menu is ready
        time.sleep(self.config['menu_wait_time'])
        
        # Press the start key (4)
        logger.info(f"Pressing '{self.config['menu_start_key']}' to start game...")
        self._press_key(self.config['menu_start_key'])
        
        # Update game state
        self.game_state = "playing"
        self.game_start_time = time.time()
        self.game_count += 1
        
        logger.info(f"Started game #{self.game_count}")
        
        # Wait for game to load properly
        time.sleep(10.0)  # Wait 10 seconds for game to fully load and be ready
    
    def _click_play_again(self):
        """Click the play again button"""
        pos = self.config['play_again_position']
        
        try:
            pyautogui.click(pos['x'], pos['y'])
            logger.info(f"Clicked play again at ({pos['x']}, {pos['y']})")
            
            # Wait for menu or new game to load
            time.sleep(2.0)
            
            # Reset game state
            self.game_state = "menu"
            self.game_start_time = None
            
            return True
        except Exception as e:
            logger.error(f"Failed to click play again: {e}")
            return False
    
    def _detect_game_over(self) -> bool:
        """Detect if the game is over using OCR or timeout"""
        if not self.config['end_game_detection']['enabled']:
            return False
        
        method = self.config['end_game_detection']['method']
        
        # Always check timeout as a fallback
        if self.game_start_time:
            elapsed = time.time() - self.game_start_time
            if elapsed > self.config['end_game_detection']['timeout_seconds']:
                logger.info(f"Game timeout reached ({elapsed:.1f}s) - using timeout detection")
                return True
        
        if method == "ocr":
            try:
                # Capture current screen
                monitor = self.sct.monitors[self.config['monitor_index']]
                screenshot = self.sct.grab(monitor)
                
                # Convert to numpy array for OCR
                img = np.array(screenshot)
                
                # Run OCR detection
                detection = self.game_over_detector.detect(img)
                
                if detection.is_game_over:
                    logger.info(f"Game over detected via OCR (confidence: {detection.confidence:.2f})")
                    
                    # Handle Quit button
                    if detection.has_quit_button and not self.quit_clicked:
                        center = self.game_over_detector.get_button_center(detection.quit_button_location)
                        if center:
                            logger.info(f"Clicking Quit button at {center}")
                            pyautogui.click(center[0], center[1])
                            self.quit_clicked = True
                            time.sleep(2.0)  # Wait for transition
                    
                    # Handle Play Again button (only if quit was clicked)
                    elif detection.has_play_again_button and self.quit_clicked:
                        center = self.game_over_detector.get_button_center(detection.play_again_button_location)
                        if center:
                            logger.info(f"Clicking Play Again button at {center}")
                            pyautogui.click(center[0], center[1])
                            self.quit_clicked = False  # Reset for next game
                            time.sleep(2.0)  # Wait for menu to load
                            return True  # Game is over, we're back to menu
                    
                    return True
                    
            except Exception as e:
                logger.error(f"OCR detection failed: {e}")
                # Fall back to timeout detection
        
        elif method == "pixel":
            # TODO: Implement pixel-based detection if needed
            pass
        
        return False
    
    def capture_screenshot_with_action(self) -> Dict[str, Any]:
        """Capture a screenshot with an action beforehand"""
        # Make random choice before screenshot if in game
        actions_made = None
        if self.game_state == "playing" and self.config['choice_before_screenshot']:
            logger.info("Making random choice(s) before screenshot...")
            actions_made = self._make_random_choice()
        
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
            "game_number": self.game_count,
            "game_state": self.game_state,
            "actions_made": actions_made,
            "time_in_game": (time.time() - self.game_start_time) if self.game_start_time else None,
            "width": screenshot.width,
            "height": screenshot.height,
            "monitor_region": {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"]
            }
        }
        
        self.screenshot_count += 1
        self.metadata.append(metadata)

        logger.info(f"Captured screenshot {self.screenshot_count} (Game {self.game_count}, Actions: {actions_made})")
        
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
            "total_games": self.game_count,
            "config": self.config,
            "screenshots": self.metadata
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(session_metadata, f, indent=2)
        
        logger.debug(f"Saved metadata for {self.screenshot_count} screenshots")
    
    def check_stop_conditions(self) -> bool:
        """Check if collection should stop"""
        # Check for stop file
        if self.stop_file.exists():
            logger.info(f"Stop file detected: {self.stop_file}")
            self.stop_file.unlink()
            return True
        
        # Check game limit - only stop if we've actually played games and reached the limit
        # Don't stop immediately if game_count is 0
        if self.game_count > 0 and self.game_count >= self.config['games_per_session']:
            logger.info(f"Reached game limit ({self.config['games_per_session']})")
            return True
        
        return False
    
    def run_automated_session(self):
        """Run the main automated collection loop"""
        logger.info(f"Starting automated collection session")
        logger.info(f"Target: {self.config['games_per_session']} games or {self.config['session_duration']} seconds")
        logger.info("=" * 60)
        logger.info("TO STOP COLLECTION:")
        logger.info("  1. Press Ctrl+C")
        logger.info(f"  2. Create file: {self.stop_file}")
        logger.info("     Run: touch STOP_AUTO_COLLECTOR")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Initial wait for user to position game window
        logger.info("Starting in 5 seconds... Please switch to the game window!")
        time.sleep(5)
        
        logger.info(f"Initial state: {self.game_state}, Game count: {self.game_count}")
        
        try:
            while self.running and (time.time() - start_time < self.config['session_duration']):
                # Check stop conditions
                if self.check_stop_conditions():
                    logger.info("Stop condition detected")
                    break
                
                logger.debug(f"Current state: {self.game_state}, Game count: {self.game_count}/{self.config['games_per_session']}")
                
                # Handle different game states
                if self.game_state == "menu":
                    # Start a new game
                    logger.info(f"In menu state, starting game #{self.game_count + 1}")
                    self._start_game_from_menu()
                    
                elif self.game_state == "playing":
                    # Capture screenshot with action
                    self.capture_screenshot_with_action()
                    
                    # Check if game is over
                    if self._detect_game_over():
                        logger.info("Game over detected")
                        self.game_state = "game_over"
                    
                    # Wait for next capture
                    if self.config['randomize_intervals']:
                        interval = random.uniform(
                            self.config['capture_interval']['min'],
                            self.config['capture_interval']['max']
                        )
                    else:
                        interval = self.config['capture_interval']['min']
                    
                    time.sleep(interval)
                    
                elif self.game_state == "game_over":
                    # Try to click play again
                    if self._click_play_again():
                        self.game_state = "menu"
                    else:
                        # If play again fails, wait and try again
                        time.sleep(2.0)
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("\nCollection stopped by user (Ctrl+C)")
        
        finally:
            # Save final metadata
            self.save_metadata()
            self._print_summary()
    
    def _print_summary(self):
        """Print collection session summary"""
        print("\n" + "="*50)
        print("AUTOMATED COLLECTION SUMMARY")
        print("="*50)
        print(f"Session ID: {self.session_id}")
        print(f"Total games played: {self.game_count}")
        print(f"Total screenshots: {self.screenshot_count}")
        print(f"Average screenshots per game: {self.screenshot_count / max(1, self.game_count):.1f}")
        print(f"Output directory: {self.output_dir}")
        print(f"Metadata saved: {self.output_dir / 'metadata.json'}")
        print("="*50)


def create_config_file():
    """Create a sample configuration file for automated collection"""
    sample_config = {
        "output_directory": "./screenshots",
        "capture_interval": {
            "min": 30.0,  # 30 seconds between captures
            "max": 35.0
        },
        "session_duration": 1800,
        "games_per_session": 10,
        "auto_fullscreen": True,
        "capture_region": None,
        "monitor_index": 1,
        "image_format": "png",
        "metadata_save_interval": 10,
        "randomize_intervals": True,
        
        "game_window_title": None,
        "menu_start_key": "4",
        "game_choices": ["1", "2", "3"],
        "choice_before_screenshot": True,
        "choice_delay": 2.0,  # 2 seconds after making choice
        
        "play_again_position": {
            "x": 240,
            "y": 600
        },
        
        "menu_wait_time": 5.0,  # 5 seconds wait in menu
        "game_timeout": 300,
        "action_cooldown": 3.0,  # 3 seconds between actions
        
        "end_game_detection": {
            "enabled": True,
            "method": "ocr",
            "timeout_seconds": 200,
            "check_interval": 1.0
        },
        
        "random_actions": {
            "enabled": True,
            "count": 3,
            "delay_between_actions": 1.0
        }
    }
    
    config_path = Path("automated_config.json")
    
    if config_path.exists():
        print(f"Config file already exists at {config_path}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            return
    
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Created sample config file: {config_path}")
    print("Edit this file to customize automated collection settings")


def main():
    """Main entry point for automated collector"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automated data collector for game dataset"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--games",
        type=int,
        help="Number of games to play (overrides config)"
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
    
    args = parser.parse_args()
    
    if args.create_config:
        create_config_file()
        return
    
    # Initialize collector
    collector = AutomatedDataCollector(args.config)
    
    # Override config with command line arguments
    if args.games:
        collector.config['games_per_session'] = args.games
    
    if args.duration:
        collector.config['session_duration'] = args.duration
    
    if args.output:
        collector.config['output_directory'] = args.output
        collector.output_dir = Path(args.output) / collector.session_id
        collector.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run collection
    print("\n" + "="*50)
    print("AUTOMATED DATA COLLECTOR")
    print("="*50)
    print(f"Games target: {collector.config['games_per_session']}")
    print(f"Duration: {collector.config['session_duration']} seconds")
    print(f"Output: {collector.output_dir}")
    print("="*50)
    print("\nPlease switch to the game window...")
    print("Collection will start in 5 seconds...")
    
    collector.run_automated_session()


if __name__ == "__main__":
    main()