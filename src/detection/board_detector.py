import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import torch
import torchvision.transforms as transforms
from PIL import Image

@dataclass
class Unit:
    name: str
    level: int
    position: Tuple[int, int]
    hp: Optional[int] = None
    items: List[str] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []

class BoardDetector:
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        if model_path:
            self.load_model(model_path)
        
        self.board_size = (7, 4)
        
        self.unit_templates = {}
        
        self.transform = transforms.Compose([
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def load_model(self, model_path: str):
        self.model = torch.load(model_path, map_location='cpu')
        self.model.eval()
    
    def detect_units(self, board_image: np.ndarray) -> List[Unit]:
        units = []
        
        grid_positions = self._get_grid_positions(board_image)
        
        for row, col in grid_positions:
            unit_region = self._extract_grid_cell(board_image, row, col)
            
            if self._is_occupied(unit_region):
                unit = self._identify_unit(unit_region, (row, col))
                if unit:
                    units.append(unit)
        
        return units
    
    def _get_grid_positions(self, board_image: np.ndarray) -> List[Tuple[int, int]]:
        h, w = board_image.shape[:2]
        
        positions = []
        
        rows, cols = self.board_size
        cell_height = h // rows
        cell_width = w // cols
        
        for row in range(rows):
            for col in range(cols):
                if self._is_valid_position(row, col):
                    positions.append((row, col))
        
        return positions
    
    def _is_valid_position(self, row: int, col: int) -> bool:
        if row < 2:
            return 1 <= col <= 5
        else:
            return 0 <= col <= 6
    
    def _extract_grid_cell(self, board_image: np.ndarray, row: int, col: int) -> np.ndarray:
        h, w = board_image.shape[:2]
        rows, cols = self.board_size
        
        cell_height = h // rows
        cell_width = w // cols
        
        y1 = row * cell_height
        y2 = (row + 1) * cell_height
        x1 = col * cell_width
        x2 = (col + 1) * cell_width
        
        return board_image[y1:y2, x1:x2]
    
    def _is_occupied(self, cell_image: np.ndarray) -> bool:
        gray = cv2.cvtColor(cell_image, cv2.COLOR_RGB2GRAY)
        
        edges = cv2.Canny(gray, 50, 150)
        
        num_edges = np.sum(edges > 0)
        
        threshold = cell_image.shape[0] * cell_image.shape[1] * 0.05
        
        return num_edges > threshold
    
    def _identify_unit(self, unit_image: np.ndarray, position: Tuple[int, int]) -> Optional[Unit]:
        if self.model is None:
            return self._identify_unit_template(unit_image, position)
        
        pil_image = Image.fromarray(unit_image)
        tensor = self.transform(pil_image).unsqueeze(0)
        
        with torch.no_grad():
            output = self.model(tensor)
            predicted_class = torch.argmax(output, dim=1).item()
        
        unit_name = self._class_to_unit_name(predicted_class)
        level = self._detect_level(unit_image)
        
        return Unit(
            name=unit_name,
            level=level,
            position=position
        )
    
    def _identify_unit_template(self, unit_image: np.ndarray, position: Tuple[int, int]) -> Optional[Unit]:
        level = self._detect_level(unit_image)
        
        return Unit(
            name="Unknown",
            level=level,
            position=position
        )
    
    def _detect_level(self, unit_image: np.ndarray) -> int:
        h, w = unit_image.shape[:2]
        
        level_region = unit_image[int(h*0.7):int(h*0.9), int(w*0.4):int(w*0.6)]
        
        gray = cv2.cvtColor(level_region, cv2.COLOR_RGB2GRAY)
        
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        star_count = self._count_stars(thresh)
        
        return min(star_count, 3)
    
    def _count_stars(self, binary_image: np.ndarray) -> int:
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        star_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if 10 < area < 200:
                star_count += 1
        
        return star_count
    
    def _class_to_unit_name(self, class_id: int) -> str:
        unit_names = {
            0: "Warrior",
            1: "Mage",
            2: "Archer",
            3: "Tank",
            4: "Assassin",
            5: "Support"
        }
        return unit_names.get(class_id, "Unknown")
    
    def visualize_detection(self, board_image: np.ndarray, units: List[Unit]) -> np.ndarray:
        vis_image = board_image.copy()
        h, w = board_image.shape[:2]
        rows, cols = self.board_size
        
        cell_height = h // rows
        cell_width = w // cols
        
        for unit in units:
            row, col = unit.position
            x1 = col * cell_width
            y1 = row * cell_height
            x2 = (col + 1) * cell_width
            y2 = (row + 1) * cell_height
            
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            label = f"{unit.name} L{unit.level}"
            cv2.putText(vis_image, label, (x1 + 5, y1 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return vis_image