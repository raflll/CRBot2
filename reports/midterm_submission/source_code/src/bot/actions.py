import pyautogui
import time
from typing import Tuple, Optional

class GameActions:
    def __init__(self):
        self.shop_positions = [(160, 700), (240, 700), (320, 700)]
        self.exp_button_pos = (400, 700)
        self.sell_area_pos = (240, 800)
        
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def buy_shop_card(self, index: int):
        if 0 <= index < len(self.shop_positions):
            pyautogui.click(self.shop_positions[index])
    
    def buy_exp(self):
        pyautogui.click(self.exp_button_pos)
    
    def move_unit(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        pyautogui.moveTo(from_pos[0], from_pos[1])
        pyautogui.dragTo(to_pos[0], to_pos[1], duration=0.5, button='left')
    
    def sell_unit(self, unit_position: Tuple[int, int]):
        pyautogui.moveTo(unit_position[0], unit_position[1])
        pyautogui.dragTo(self.sell_area_pos[0], self.sell_area_pos[1], 
                        duration=0.5, button='left')
    
    def move_to_carousel_item(self, target_pos: Optional[Tuple[int, int]] = None):
        if target_pos:
            pyautogui.rightClick(target_pos[0], target_pos[1])
        else:
            pyautogui.rightClick(240, 400)
    
    def place_item(self, item_pos: Tuple[int, int], unit_pos: Tuple[int, int]):
        pyautogui.moveTo(item_pos[0], item_pos[1])
        pyautogui.dragTo(unit_pos[0], unit_pos[1], duration=0.3, button='left')
    
    def combine_items(self, item1_pos: Tuple[int, int], item2_pos: Tuple[int, int]):
        pyautogui.moveTo(item1_pos[0], item1_pos[1])
        pyautogui.dragTo(item2_pos[0], item2_pos[1], duration=0.3, button='left')
    
    def keyboard_action(self, key: str):
        pyautogui.press(key)