from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import time

class GamePhase(Enum):
    PLANNING = "planning"
    BATTLE = "battle"
    CAROUSEL = "carousel"
    DRAFT = "draft"
    LOADING = "loading"
    MENU = "menu"

@dataclass
class GameState:
    phase: GamePhase = GamePhase.MENU
    round_number: int = 0
    gold: int = 0
    health: int = 100
    level: int = 1
    exp: int = 0
    board_units: List = field(default_factory=list)
    bench_units: List = field(default_factory=list)
    shop_cards: List = field(default_factory=list)
    items: List = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.timestamp = time.time()
    
    def can_buy(self, cost: int) -> bool:
        return self.gold >= cost
    
    def has_bench_space(self) -> bool:
        return len(self.bench_units) < 9
    
    def has_board_space(self) -> bool:
        return len(self.board_units) < self.level
    
    def get_unit_count(self, unit_name: str) -> int:
        count = 0
        for unit in self.board_units + self.bench_units:
            if unit.name == unit_name:
                count += 1
        return count
    
    def can_upgrade_unit(self, unit_name: str) -> bool:
        return self.get_unit_count(unit_name) >= 3
    
    def should_level_up(self) -> bool:
        if self.gold >= 4 and self.level < 9:
            if self.level < 5 and self.gold >= 4:
                return True
            elif self.level >= 5 and self.gold >= 8:
                return True
        return False
    
    
    def get_strategy_phase(self) -> str:
        if self.round_number <= 5:
            return "early"
        elif self.round_number <= 15:
            return "mid"
        else:
            return "late"

class GameStateHistory:
    def __init__(self, max_history: int = 100):
        self.states: List[GameState] = []
        self.max_history = max_history
    
    def add_state(self, state: GameState):
        self.states.append(state)
        if len(self.states) > self.max_history:
            self.states.pop(0)
    
    def get_latest(self) -> Optional[GameState]:
        return self.states[-1] if self.states else None
    
    def get_previous(self, n: int = 1) -> Optional[GameState]:
        if len(self.states) > n:
            return self.states[-(n+1)]
        return None
    
    def detect_phase_change(self) -> bool:
        if len(self.states) >= 2:
            return self.states[-1].phase != self.states[-2].phase
        return False
    
    def get_gold_trend(self, window: int = 5) -> float:
        if len(self.states) < window:
            return 0
        
        recent_gold = [s.gold for s in self.states[-window:]]
        return sum(recent_gold) / len(recent_gold)
    
    def get_health_lost_recently(self, window: int = 3) -> int:
        if len(self.states) < window:
            return 0
        
        start_health = self.states[-window].health
        current_health = self.states[-1].health
        return max(0, start_health - current_health)