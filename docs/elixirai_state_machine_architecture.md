# ElixirAI State Machine Architecture

## Overview
The ElixirAI bot uses a hierarchical state machine architecture to manage game flow, decision-making, and action execution. This design provides clear separation of concerns, easier debugging, and extensible gameplay logic.

## Core State Machine Design

### State Machine Hierarchy

```
MainStateMachine
├── MenuNavigationStateMachine
│   ├── MAIN_MENU
│   ├── GAME_MODE_SELECT
│   └── LOADING
├── GameStateMachine
│   ├── PRE_GAME
│   ├── IN_GAME
│   │   ├── DeployPhaseStateMachine
│   │   └── BattlePhaseStateMachine
│   ├── POST_GAME
│   └── ERROR_RECOVERY
└── MetaStateMachine
    ├── COLLECTING_DATA
    ├── TRAINING
    └── ANALYZING
```

## Detailed State Definitions

### 1. Main State Machine
The top-level controller that manages the overall bot lifecycle.

```python
class MainState(Enum):
    INITIALIZATION = "initialization"
    MENU_NAVIGATION = "menu_navigation"
    IN_GAME = "in_game"
    META_OPERATIONS = "meta_operations"
    SHUTDOWN = "shutdown"
    ERROR = "error"
```

### 2. Menu Navigation States
Handles all out-of-game navigation and setup.

```python
class MenuState(Enum):
    DETECTING_SCREEN = "detecting_screen"
    MAIN_MENU = "main_menu"
    SELECTING_MODE = "selecting_mode"
    FINDING_MATCH = "finding_match"
    LOADING_GAME = "loading_game"
    RECONNECTING = "reconnecting"
    HANDLING_POPUP = "handling_popup"
```

### 3. Game States
Core gameplay state management during matches.

```python
class GameState(Enum):
    # Pre-game states
    ROUND_STARTING = "round_starting"
    ANALYZING_OPPONENTS = "analyzing_opponents"
    INITIAL_SETUP = "initial_setup"
    
    # Deploy phase states
    DEPLOY_PHASE_START = "deploy_phase_start"
    EVALUATING_SHOP = "evaluating_shop"
    BUYING_TROOPS = "buying_troops"
    MERGING_TROOPS = "merging_troops"
    POSITIONING_TROOPS = "positioning_troops"
    MANAGING_RESERVE = "managing_reserve"
    OPTIMIZING_TRAITS = "optimizing_traits"
    DEPLOY_PHASE_END = "deploy_phase_end"
    
    # Battle phase states
    BATTLE_PHASE_START = "battle_phase_start"
    WATCHING_BATTLE = "watching_battle"
    QUICK_SHOPPING = "quick_shopping"
    RESERVE_MANAGEMENT = "reserve_management"
    BATTLE_PHASE_END = "battle_phase_end"
    
    # Post-round states
    CALCULATING_DAMAGE = "calculating_damage"
    UPDATING_STRATEGY = "updating_strategy"
    ROUND_COMPLETE = "round_complete"
    
    # End game states
    GAME_WON = "game_won"
    GAME_LOST = "game_lost"
    ANALYZING_RESULTS = "analyzing_results"
```

### 4. Deploy Phase Sub-States
Detailed states for the deployment phase actions.

```python
class DeployPhaseState(Enum):
    SCANNING_BOARD = "scanning_board"
    IDENTIFYING_MERGES = "identifying_merges"
    CALCULATING_PURCHASES = "calculating_purchases"
    EXECUTING_MERGE = "executing_merge"
    EXECUTING_PURCHASE = "executing_purchase"
    MOVING_TO_ARENA = "moving_to_arena"
    MOVING_TO_RESERVE = "moving_to_reserve"
    VALIDATING_POSITION = "validating_position"
    CHECKING_TRAITS = "checking_traits"
    FINALIZING_DEPLOYMENT = "finalizing_deployment"
```

### 5. Battle Phase Sub-States
States specific to battle phase observation and limited actions.

```python
class BattlePhaseState(Enum):
    OBSERVING_COMBAT = "observing_combat"
    TRACKING_DAMAGE = "tracking_damage"
    ANALYZING_ENEMY_COMP = "analyzing_enemy_comp"
    EMERGENCY_PURCHASE = "emergency_purchase"
    RESERVE_SWAP = "reserve_swap"
    PREPARING_NEXT_ROUND = "preparing_next_round"
```

## State Transitions

### Transition Rules
Each state has defined valid transitions to prevent illegal state changes.

```python
class StateTransition:
    def __init__(self, from_state, to_state, condition, action=None):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition  # Function that returns bool
        self.action = action  # Optional action to execute on transition

# Example transitions
transitions = [
    StateTransition(
        from_state=GameState.DEPLOY_PHASE_START,
        to_state=GameState.EVALUATING_SHOP,
        condition=lambda ctx: ctx.phase_timer > 0,
        action=lambda ctx: ctx.scan_shop()
    ),
    StateTransition(
        from_state=GameState.EVALUATING_SHOP,
        to_state=GameState.BUYING_TROOPS,
        condition=lambda ctx: ctx.has_purchase_targets(),
        action=lambda ctx: ctx.execute_purchases()
    ),
    StateTransition(
        from_state=GameState.BUYING_TROOPS,
        to_state=GameState.MERGING_TROOPS,
        condition=lambda ctx: ctx.has_mergeable_troops(),
        action=lambda ctx: ctx.identify_merges()
    ),
]
```

## State Machine Implementation

### Base State Machine Class
```python
from enum import Enum
from typing import Dict, List, Optional, Callable
import logging
from datetime import datetime

class StateMachine:
    def __init__(self, name: str, initial_state: Enum):
        self.name = name
        self.current_state = initial_state
        self.previous_state = None
        self.transitions: Dict[Enum, List[StateTransition]] = {}
        self.state_handlers: Dict[Enum, Callable] = {}
        self.entry_actions: Dict[Enum, Callable] = {}
        self.exit_actions: Dict[Enum, Callable] = {}
        self.state_history = []
        self.logger = logging.getLogger(f"StateMachine.{name}")
        
    def register_transition(self, transition: StateTransition):
        """Register a valid state transition"""
        if transition.from_state not in self.transitions:
            self.transitions[transition.from_state] = []
        self.transitions[transition.from_state].append(transition)
    
    def register_state_handler(self, state: Enum, handler: Callable):
        """Register a handler function for a state"""
        self.state_handlers[state] = handler
    
    def register_entry_action(self, state: Enum, action: Callable):
        """Register an action to execute when entering a state"""
        self.entry_actions[state] = action
    
    def register_exit_action(self, state: Enum, action: Callable):
        """Register an action to execute when leaving a state"""
        self.exit_actions[state] = action
    
    def update(self, context):
        """Update the state machine with current context"""
        # Execute current state handler
        if self.current_state in self.state_handlers:
            self.state_handlers[self.current_state](context)
        
        # Check for valid transitions
        if self.current_state in self.transitions:
            for transition in self.transitions[self.current_state]:
                if transition.condition(context):
                    self.transition_to(transition.to_state, context, transition.action)
                    break
    
    def transition_to(self, new_state: Enum, context, action: Optional[Callable] = None):
        """Execute a state transition"""
        # Log transition
        self.logger.info(f"Transitioning from {self.current_state} to {new_state}")
        self.state_history.append({
            'from': self.current_state,
            'to': new_state,
            'timestamp': datetime.now()
        })
        
        # Execute exit action for current state
        if self.current_state in self.exit_actions:
            self.exit_actions[self.current_state](context)
        
        # Update states
        self.previous_state = self.current_state
        self.current_state = new_state
        
        # Execute transition action if provided
        if action:
            action(context)
        
        # Execute entry action for new state
        if new_state in self.entry_actions:
            self.entry_actions[new_state](context)
    
    def force_state(self, state: Enum):
        """Force transition to a specific state (use with caution)"""
        self.logger.warning(f"Force transitioning to {state}")
        self.previous_state = self.current_state
        self.current_state = state
    
    def get_state_duration(self) -> float:
        """Get how long we've been in the current state"""
        if self.state_history:
            last_transition = self.state_history[-1]['timestamp']
            return (datetime.now() - last_transition).total_seconds()
        return 0.0
```

### Game-Specific State Machine
```python
class ElixirAIGameStateMachine(StateMachine):
    def __init__(self):
        super().__init__("ElixirAIGame", GameState.ROUND_STARTING)
        self._setup_states()
        self._setup_transitions()
    
    def _setup_states(self):
        # Deploy phase handlers
        self.register_state_handler(
            GameState.EVALUATING_SHOP,
            self._handle_shop_evaluation
        )
        self.register_state_handler(
            GameState.BUYING_TROOPS,
            self._handle_troop_purchase
        )
        self.register_state_handler(
            GameState.MERGING_TROOPS,
            self._handle_troop_merging
        )
        
        # Battle phase handlers
        self.register_state_handler(
            GameState.WATCHING_BATTLE,
            self._handle_battle_observation
        )
        
        # Entry/Exit actions
        self.register_entry_action(
            GameState.DEPLOY_PHASE_START,
            lambda ctx: self.logger.info("Deploy phase started")
        )
        self.register_exit_action(
            GameState.DEPLOY_PHASE_END,
            lambda ctx: ctx.save_deployment_state()
        )
    
    def _setup_transitions(self):
        # Deploy phase transitions
        self.register_transition(StateTransition(
            GameState.DEPLOY_PHASE_START,
            GameState.EVALUATING_SHOP,
            lambda ctx: ctx.shop_visible()
        ))
        
        self.register_transition(StateTransition(
            GameState.EVALUATING_SHOP,
            GameState.BUYING_TROOPS,
            lambda ctx: len(ctx.purchase_queue) > 0
        ))
        
        self.register_transition(StateTransition(
            GameState.BUYING_TROOPS,
            GameState.MERGING_TROOPS,
            lambda ctx: ctx.has_mergeable_pairs()
        ))
        
        self.register_transition(StateTransition(
            GameState.MERGING_TROOPS,
            GameState.POSITIONING_TROOPS,
            lambda ctx: not ctx.has_mergeable_pairs()
        ))
        
        # Battle phase transitions
        self.register_transition(StateTransition(
            GameState.DEPLOY_PHASE_END,
            GameState.BATTLE_PHASE_START,
            lambda ctx: ctx.battle_started()
        ))
        
        self.register_transition(StateTransition(
            GameState.BATTLE_PHASE_END,
            GameState.CALCULATING_DAMAGE,
            lambda ctx: ctx.battle_ended()
        ))
    
    def _handle_shop_evaluation(self, context):
        """Evaluate shop and determine purchases"""
        shop_items = context.detect_shop_items()
        context.purchase_queue = context.strategy.evaluate_purchases(
            shop_items,
            context.current_board,
            context.elixir
        )
    
    def _handle_troop_purchase(self, context):
        """Execute troop purchases from shop"""
        while context.purchase_queue and context.elixir >= 3:
            purchase = context.purchase_queue.pop(0)
            success = context.execute_action(purchase)
            if success:
                context.elixir -= purchase.cost
                context.update_board_state()
    
    def _handle_troop_merging(self, context):
        """Execute troop merges"""
        merge_pairs = context.identify_merge_pairs()
        for merge in merge_pairs:
            success = context.execute_merge(merge)
            if success:
                context.elixir += 1  # Merging gives 1 elixir
                context.update_board_state()
    
    def _handle_battle_observation(self, context):
        """Observe battle and collect data"""
        context.track_battle_progress()
        context.analyze_enemy_strategies()
        context.predict_battle_outcome()
```

## Context System

### Game Context
Maintains all game-related information needed by the state machine.

```python
class GameContext:
    def __init__(self):
        # Game state
        self.round_number = 0
        self.phase = None  # "deploy" or "battle"
        self.phase_timer = 0
        
        # Resources
        self.elixir = 4
        self.ruler_hp = 10
        
        # Board state
        self.arena_troops = []  # Troops in arena
        self.reserve_troops = []  # Troops in reserve
        self.shop_items = []  # Current shop offerings
        
        # Enemy information
        self.enemy_boards = {}  # Dict of enemy_id -> board_state
        self.enemy_hp = {}  # Dict of enemy_id -> hp
        
        # Action queues
        self.purchase_queue = []
        self.merge_queue = []
        self.position_queue = []
        
        # Strategy and AI
        self.strategy = None  # Current strategy object
        self.predictions = {}  # Battle predictions
        
        # Detection results
        self.last_detection = None
        self.detection_confidence = 0.0
        
    def update_from_detection(self, detection_result):
        """Update context from computer vision detection"""
        self.last_detection = detection_result
        self.phase = detection_result.phase
        self.elixir = detection_result.elixir
        self.ruler_hp = detection_result.ruler_hp
        self.arena_troops = detection_result.arena_troops
        self.reserve_troops = detection_result.reserve_troops
        self.shop_items = detection_result.shop_items
```

## Error Recovery States

### Error Handling State Machine
Handles unexpected situations and recovery.

```python
class ErrorState(Enum):
    DETECTION_FAILED = "detection_failed"
    ACTION_FAILED = "action_failed"
    DESYNC_DETECTED = "desync_detected"
    CONNECTION_LOST = "connection_lost"
    RECOVERING = "recovering"
    RESYNCING = "resyncing"

class ErrorRecoveryStateMachine(StateMachine):
    def __init__(self):
        super().__init__("ErrorRecovery", ErrorState.DETECTING_ERROR)
        
    def handle_detection_failure(self, context):
        """Recover from vision detection failures"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            # Try alternative detection methods
            if context.try_alternative_detection():
                return self.transition_to(GameState.SCANNING_BOARD)
            retry_count += 1
        
        # If all retries fail, restart game
        return self.transition_to(ErrorState.RESTARTING_GAME)
```

## Strategy Integration

### Strategy Pattern with State Machine
Different strategies can be plugged into the state machine.

```python
class Strategy:
    def evaluate_purchases(self, shop, board, elixir):
        raise NotImplementedError
    
    def identify_merges(self, board):
        raise NotImplementedError
    
    def position_troops(self, troops, arena_slots):
        raise NotImplementedError

class AggressiveStrategy(Strategy):
    """Focus on high-damage troops and quick merges"""
    pass

class DefensiveStrategy(Strategy):
    """Focus on tanky troops and trait synergies"""
    pass

class AdaptiveStrategy(Strategy):
    """Adapts based on opponent compositions"""
    pass
```

## Monitoring and Debugging

### State Machine Monitor
```python
class StateMachineMonitor:
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        self.state_durations = {}
        self.transition_counts = {}
        self.error_states = []
        
    def log_state_info(self):
        """Log current state information"""
        current = self.state_machine.current_state
        duration = self.state_machine.get_state_duration()
        
        logging.info(f"""
        State Machine: {self.state_machine.name}
        Current State: {current}
        Duration: {duration:.2f}s
        Previous State: {self.state_machine.previous_state}
        Total Transitions: {len(self.state_machine.state_history)}
        """)
    
    def detect_stuck_states(self, max_duration=30):
        """Detect if stuck in a state too long"""
        duration = self.state_machine.get_state_duration()
        if duration > max_duration:
            logging.warning(f"Stuck in state {self.state_machine.current_state} for {duration}s")
            return True
        return False
```

## Future State Expansions

### Planned Additional States

1. **Learning States**
   - COLLECTING_TRAINING_DATA
   - ANALYZING_OPPONENT_PATTERNS
   - UPDATING_MODEL

2. **Tournament States**
   - TOURNAMENT_LOBBY
   - DRAFTING_PHASE
   - SPECTATING_MATCH

3. **Meta-Game States**
   - ANALYZING_META
   - ADJUSTING_STRATEGY
   - TESTING_COUNTERS

4. **Advanced Combat States**
   - PREDICTING_OUTCOME
   - EMERGENCY_ADJUSTMENT
   - SACRIFICIAL_ROUND

5. **Optimization States**
   - CALCULATING_OPTIMAL_PATH
   - SIMULATING_OUTCOMES
   - RESOURCE_OPTIMIZATION

## Implementation Notes

### Best Practices
1. **Single Responsibility**: Each state should handle one specific aspect
2. **Clear Transitions**: Transition conditions should be explicit and testable
3. **Logging**: Every state change should be logged for debugging
4. **Timeouts**: All states should have maximum duration limits
5. **Error Recovery**: Every state should have error handling paths

### Performance Considerations
1. **State Update Frequency**: 10-30 Hz for game states, 1-5 Hz for menu states
2. **Context Caching**: Cache expensive computations in context
3. **Async Operations**: Use async for long-running operations
4. **Memory Management**: Clear old state history periodically

### Testing Strategy
1. **Unit Tests**: Test each state handler independently
2. **Transition Tests**: Verify all transition conditions
3. **Integration Tests**: Test full state sequences
4. **Simulation Tests**: Test against game simulator
5. **Recovery Tests**: Test error recovery paths