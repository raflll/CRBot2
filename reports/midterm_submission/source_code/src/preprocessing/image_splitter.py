import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any
import cv2

class GameScreenSplitter:
    def __init__(self, screen_width: int = 480, screen_height: int = 848):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.board_region = {
            'top': int(screen_height * 0.15),
            'bottom': int(screen_height * 0.65),
            'left': 0,
            'right': screen_width
        }
        
        self.shop_region = {
            'top': int(screen_height * 0.72),
            'bottom': int(screen_height * 0.85),
            'left': int(screen_width * 0.15),
            'right': int(screen_width * 0.85)
        }
        
        self.gold_region = {
            'top': int(screen_height * 0.83),
            'bottom': int(screen_height * 0.88),
            'left': int(screen_width * 0.85),
            'right': int(screen_width * 0.95)
        }
        
        self.bench_region = {
            'top': int(screen_height * 0.58),
            'bottom': int(screen_height * 0.65),
            'left': int(screen_width * 0.1),
            'right': int(screen_width * 0.9)
        }
    
    def split_screenshot(self, image_path: str) -> Dict[str, np.ndarray]:
        img = Image.open(image_path)
        img_array = np.array(img)
        return self.split_screenshot_array(img_array)
    
    def split_screenshot_array(self, img_array: np.ndarray) -> Dict[str, np.ndarray]:
        
        regions = {}
        
        board = img_array[
            self.board_region['top']:self.board_region['bottom'],
            self.board_region['left']:self.board_region['right']
        ]
        regions['board'] = board
        
        shop = img_array[
            self.shop_region['top']:self.shop_region['bottom'],
            self.shop_region['left']:self.shop_region['right']
        ]
        regions['shop'] = shop
        
        gold = img_array[
            self.gold_region['top']:self.gold_region['bottom'],
            self.gold_region['left']:self.gold_region['right']
        ]
        regions['gold'] = gold
        
        bench = img_array[
            self.bench_region['top']:self.bench_region['bottom'],
            self.bench_region['left']:self.bench_region['right']
        ]
        regions['bench'] = bench
        
        return regions
    
    def extract_shop_cards(self, shop_region: np.ndarray, num_cards: int = 3) -> list:
        h, w = shop_region.shape[:2]
        card_width = w // num_cards
        
        cards = []
        for i in range(num_cards):
            card = shop_region[:, i * card_width:(i + 1) * card_width]
            cards.append(card)
        
        return cards
    
    def extract_board_units(self, board_region: np.ndarray) -> list:
        gray = cv2.cvtColor(board_region, cv2.COLOR_RGB2GRAY)
        
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        units = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                unit = board_region[y:y+h, x:x+w]
                units.append({
                    'image': unit,
                    'position': (x, y),
                    'size': (w, h)
                })
        
        return units
    
    def save_regions(self, regions: Dict[str, np.ndarray], output_dir: str):
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for name, region in regions.items():
            img = Image.fromarray(region)
            img.save(f"{output_dir}/{name}.png")