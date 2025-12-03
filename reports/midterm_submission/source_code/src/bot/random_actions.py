import random
import time
import pyautogui
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RandomActionGenerator:
    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def perform_buy_shop_card(self):
        """Randomly buy a shop card by pressing 1, 2, or 3"""
        card_index = random.randint(0, 2)
        key = str(card_index + 1)  # Convert to '1', '2', or '3'
        
        logger.debug(f"Pressing '{key}' to buy shop card {card_index + 1}")
        pyautogui.press(key)
        return f"press_{key}"
    
    def perform_random_action(self):
        """Perform a random game action - just pressing 1, 2, or 3"""
        # Just randomly press 1, 2, or 3 to simulate buying cards
        result = self.perform_buy_shop_card()
        return result
    
    def perform_action_sequence(self, config: Dict[str, Any]):
        if not config.get('enabled', False):
            return []
        
        count = config.get('count', 3)
        delay = config.get('delay_between_actions', 1.0)
        
        performed_actions = []
        
        logger.info(f"Performing {count} random actions (pressing 1, 2, or 3)")
        
        for i in range(count):
            action = self.perform_random_action()
            if action:
                performed_actions.append(action)
                logger.info(f"Action {i+1}/{count}: {action}")
            
            if i < count - 1:
                time.sleep(delay)
        
        return performed_actions