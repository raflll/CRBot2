import time
import numpy as np
from typing import Optional, Dict, List
import mss
import pyautogui
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocessing.image_splitter import GameScreenSplitter
from src.detection.board_detector import BoardDetector
from src.detection.shop_detector import ShopDetector
from src.detection.gold_detector import ResourceDetector
from src.bot.game_state import GameState, GameStateHistory, GamePhase
from src.bot.actions import GameActions

class AutoBattlerBot:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        
        self.screen_splitter = GameScreenSplitter()
        self.board_detector = BoardDetector()
        self.shop_detector = ShopDetector()
        self.resource_detector = ResourceDetector()
        
        self.game_state = GameState()
        self.state_history = GameStateHistory()
        
        self.actions = GameActions()
        
        self.running = False
        self.screenshot_monitor = mss.mss()
        
        self.strategy = self.config.get('strategy', {})
    
    def _default_config(self) -> Dict:
        return {
            'screen_region': {'top': 0, 'left': 0, 'width': 480, 'height': 848},
            'update_interval': 0.5,
            'action_delay': 0.2,
            'strategy': {
                'priority_units': [],
                'max_cost': 3,
                'aggressive_leveling': False,
                'economy_focused': True
            },
            'debug': True
        }
    
    def start(self):
        self.running = True
        print("Bot started. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                self._update_cycle()
                time.sleep(self.config['update_interval'])
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        self.running = False
        print("Bot stopped.")
    
    def _update_cycle(self):
        screenshot = self._capture_screenshot()
        if screenshot is None:
            return
        
        self._update_game_state(screenshot)
        
        self.state_history.add_state(self.game_state)
        
        if self.game_state.phase == GamePhase.PLANNING:
            self._execute_planning_phase()
        elif self.game_state.phase == GamePhase.CAROUSEL:
            self._execute_carousel_phase()
        
        if self.config['debug']:
            self._debug_output()
    
    def _capture_screenshot(self) -> Optional[np.ndarray]:
        try:
            region = self.config['screen_region']
            screenshot = self.screenshot_monitor.grab(region)
            # MSS returns BGRA format, convert to RGB for OpenCV
            img_array = np.array(screenshot)
            # Convert BGRA to RGB (swap B and R channels, remove A)
            rgb_array = img_array[:, :, [2, 1, 0]]  # BGR to RGB conversion
            return rgb_array
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            return None
    
    def _update_game_state(self, screenshot: np.ndarray):
        regions = self.screen_splitter.split_screenshot_array(screenshot)
        
        board_units = self.board_detector.detect_units(regions['board'])
        self.game_state.board_units = board_units
        
        shop_cards = self.shop_detector.detect_shop_cards(regions['shop'])
        self.game_state.shop_cards = shop_cards
        
        resources = self.resource_detector.detect_all_resources(screenshot)
        self.game_state.gold = resources.get('gold', 0)
        self.game_state.health = resources.get('health', 100)
        self.game_state.level = resources.get('level', 1)
        
        phase = self._detect_game_phase(screenshot)
        self.game_state.phase = phase
    
    def _detect_game_phase(self, screenshot: np.ndarray) -> GamePhase:
        h, w = screenshot.shape[:2]
        
        top_region = screenshot[:int(h*0.1), :]
        gray_top = np.mean(top_region)
        
        if gray_top < 50:
            return GamePhase.LOADING
        
        if self._detect_battle_indicators(screenshot):
            return GamePhase.BATTLE
        
        if self._detect_carousel_indicators(screenshot):
            return GamePhase.CAROUSEL
        
        if self._detect_planning_indicators(screenshot):
            return GamePhase.PLANNING
        
        return GamePhase.MENU
    
    def _detect_battle_indicators(self, screenshot: np.ndarray) -> bool:
        return False
    
    def _detect_carousel_indicators(self, screenshot: np.ndarray) -> bool:
        return False
    
    def _detect_planning_indicators(self, screenshot: np.ndarray) -> bool:
        return len(self.game_state.shop_cards) > 0
    
    def _execute_planning_phase(self):
        if self.game_state.should_level_up():
            self.actions.buy_exp()
            time.sleep(self.config['action_delay'])
        
        for i, card in enumerate(self.game_state.shop_cards):
            if self._should_buy_card(card):
                self.actions.buy_shop_card(i)
                time.sleep(self.config['action_delay'])
        
        self._manage_board_positioning()
    
    def _should_buy_card(self, card) -> bool:
        if not self.game_state.can_buy(card.cost):
            return False
        
        if not self.game_state.has_bench_space():
            return False
        
        if card.name in self.strategy['priority_units']:
            return True
        
        if self.game_state.get_unit_count(card.name) >= 2:
            return True
        
        if card.cost <= 2 and self.game_state.gold > 20:
            return True
        
        return False
    
    def _manage_board_positioning(self):
        pass
    
    def _execute_carousel_phase(self):
        self.actions.move_to_carousel_item()
    
    def _debug_output(self):
        print(f"\n--- Game State ---")
        print(f"Phase: {self.game_state.phase.value}")
        print(f"Gold: {self.game_state.gold}")
        print(f"Health: {self.game_state.health}")
        print(f"Level: {self.game_state.level}")
        print(f"Board Units: {len(self.game_state.board_units)}")
        print(f"Shop Cards: {[card.name for card in self.game_state.shop_cards]}")

class GameActions:
    def __init__(self):
        self.shop_positions = [(160, 700), (240, 700), (320, 700)]
        self.exp_button_pos = (400, 700)
    
    def buy_shop_card(self, index: int):
        if 0 <= index < len(self.shop_positions):
            pyautogui.click(self.shop_positions[index])
    
    def buy_exp(self):
        pyautogui.click(self.exp_button_pos)
    
    def move_unit(self, from_pos: tuple, to_pos: tuple):
        pyautogui.dragTo(to_pos[0], to_pos[1], duration=0.5, button='left')
    
    def sell_unit(self, position: tuple):
        pyautogui.dragTo(240, 800, duration=0.5, button='left')
    
    def move_to_carousel_item(self):
        pyautogui.rightClick(240, 400)

def main():
    bot = AutoBattlerBot()
    bot.start()

if __name__ == "__main__":
    main()