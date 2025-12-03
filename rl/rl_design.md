# Deep Q-Learning System Design for TacticForge

## Overview
This document outlines the design for a Deep Q-Network (DQN) reinforcement learning system that learns to make strategic card purchase decisions during the deploy phase of Clash Royale's Merge Fight Tactics mode.

### Quick Summary

| Component | Design Choice | Why |
|-----------|--------------|-----|
| **State** | 111 features (24 troops + 1 elixir + 72 card slots + 14 traits) | Includes trait features for learning synergies |
| **Actions** | 4 discrete (buy slot 1/2/3, or do nothing) | Matches game mechanics, small action space |
| **Rewards** | Two-level: ±10/round + ±100 for placement | Balances short-term tactics with long-term strategy |
| **Action Masking** | Set Q-values to `-inf` for unaffordable cards | Research-backed (Huang 2020), prevents wasted learning |
| **Costs** | Static lookup table, not in state | Game constants shouldn't be learned |
| **Network** | 4 layers (256-256-128-4) with ReLU | Handles 111 inputs, learns troop synergies and traits |
| **Training** | Experience replay (100K buffer), batch size 64 | Breaks correlation, improves stability (Mnih 2015) |
| **Exploration** | ε-greedy: 1.0 → 0.1 (decay 0.995) | Standard DQN exploration with valid actions only |

**Key Innovation**: By encoding **which troop** is in each shop slot (via one-hot), the agent learns strategic value of troops (e.g., "archers are good vs X"), not positional bias (e.g., "slot 1 is always best").

---

## Problem Formulation

### Objective
Train an agent to decide which cards to purchase from the shop during the deploy phase to maximize win rate and placement in matches.

### Action Space
The agent can take **4 discrete actions**:
1. **Action 0**: Purchase card in slot 1
2. **Action 1**: Purchase card in slot 2
3. **Action 2**: Purchase card in slot 3
4. **Action 3**: Do nothing (skip purchase)

### Action Timing
- Actions are only taken during the **deploy phase**
- Agent continues making purchase decisions until:
  - Elixir reaches 0, OR
  - Agent chooses "do nothing" (Action 3)

---

## State Representation

The state is a **111-dimensional feature vector** encoding the current game situation (uses only **24 active troops**, excluding 5 rotated out + skeleton spawned unit).

### State Vector Breakdown

| Feature Index | Description | Value Range | Encoding |
|--------------|-------------|-------------|----------|
| 0-23 | **Agent's Troop Counts (Active)** | [0, 27] | Normalized count: `min(count, 27) / 27` |
| 24 | **Current Elixir** | [0, ∞) | Normalized (see below) |
| 25-48 | **Card Slot 1 (One-Hot)** | {0, 1} | 24-dim one-hot vector for active troop type |
| 49-72 | **Card Slot 2 (One-Hot)** | {0, 1} | 24-dim one-hot vector for active troop type |
| 73-96 | **Card Slot 3 (One-Hot)** | {0, 1} | 24-dim one-hot vector for active troop type |
| 97-103 | **Primary Trait Counts** | [0, 1] | Normalized count for 7 active primary traits |
| 104-110 | **Secondary Trait Counts** | [0, 1] | Normalized count for 7 active secondary traits |

**Total State Size**: 111 features

**Excluded Troops** (NOT in state vector): archer, baby_dragon, e_wiz, giant_skeleton, knight (rotated out) + skeleton (spawned unit)

### Feature Normalization Details

#### 1. Troop Counts (indices 0-23)
Each index represents the count of one **active** troop type currently on the battlefield.
- **Active troops**: 24 troops (excludes 5 rotated out + skeleton spawned unit)
- **Max per troop**: 27 units
- **Normalization**: `min(count, 27) / 27` → range [0.0, 1.0]

#### 2. Current Elixir (index 24)
Available elixir for purchasing cards.
- **No hard maximum**: Elixir can accumulate without limit
- **Cost range**: Cards cost 2-5 elixir
- **Normalization options**:

  **Option A: Practical Maximum (Recommended if typical max known)**
  ```python
  PRACTICAL_MAX_ELIXIR = 100  # Set based on typical gameplay
  normalized_elixir = min(elixir, PRACTICAL_MAX_ELIXIR) / PRACTICAL_MAX_ELIXIR
  ```

  **Option B: Log Scaling (For unbounded elixir)**
  ```python
  ELIXIR_REFERENCE = 50  # Midpoint reference
  normalized_elixir = np.log(1 + elixir) / np.log(1 + ELIXIR_REFERENCE)
  # elixir=10 → 0.46, elixir=50 → 1.0, elixir=100 → 1.40
  ```

  **Decision needed**: What's a typical maximum elixir at deploy phase start?

#### 3. Card Slots (indices 25-96)
Each of 3 slots is encoded as a **24-dimensional one-hot vector** (active troops only):
- Exactly one index is 1.0, others are 0.0
- Index position maps to `ACTIVE_TROOP_TYPES` list (see below)

**Example**: If Slot 1 contains "dart_goblin" (index 3 in active troops):
```python
slot_1_onehot = [0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
#                     ↑ index 3
```

### Troop Type Encoding
Only **24 active troops** are indexed 0-23 (alphabetically sorted, rotated out + skeleton excluded):

```python
ACTIVE_TROOP_TYPES = [
    "archer_queen",    # 0
    "bandit",          # 1
    "barbarian",       # 2
    "dart_goblin",     # 3
    "electro_giant",   # 4
    "executioner",     # 5
    "goblin",          # 6
    "goblin_machine",  # 7
    "golden_knight",   # 8
    "mega_knight",     # 9
    "mini_pekka",      # 10
    "monk",            # 11
    "musketeer",       # 12
    "pekka",           # 13
    "prince",          # 14
    "princess",        # 15
    "royal_ghost",     # 16
    "royal_giant",     # 17
    "skeleton_dragon", # 18
    "skeleton_king",   # 19
    "spear_goblin",    # 20
    "valkyrie",        # 21
    "witch",           # 22
    "wizard"           # 23
]

# Excluded (NOT in state vector):
# - Rotated out: archer, baby_dragon, e_wiz, giant_skeleton, knight
# - Spawned unit: skeleton (not purchasable)
```

### Static Elixir Costs
Since troop costs are fixed game constants, we use a static lookup table rather than including costs in the state:

```python
# Correct elixir costs (from mergetacticsbuild.com)
ACTIVE_TROOP_COSTS = {
    "archer_queen": 5,
    "bandit": 4,
    "barbarian": 2,
    "dart_goblin": 3,
    "electro_giant": 3,
    "executioner": 3,
    "goblin": 2,
    "goblin_machine": 4,
    "golden_knight": 5,
    "mega_knight": 4,
    "mini_pekka": 2,
    "monk": 5,
    "musketeer": 3,
    "pekka": 3,
    "prince": 3,
    "princess": 4,
    "royal_ghost": 4,
    "royal_giant": 2,
    "skeleton": 0,  # Spawned unit (Trait Dummy)
    "skeleton_dragon": 2,
    "skeleton_king": 5,
    "spear_goblin": 2,
    "valkyrie": 3,
    "witch": 4,
    "wizard": 2,
}
```

**Source**: Verified costs from https://mergetacticsbuild.com/en/wiki/troops

### Trait System

Each troop has 2 traits that provide strategic bonuses when activated:
- **Primary Traits** (Origin): Ace, Clan, Giant, Goblin, Noble, P.E.K.K.A, Undead
- **Secondary Traits** (Role): Assassin, Blaster, Brawler, Brutalist, Ranger, Superstar, Thrower

**Activation Thresholds**: Traits activate at 2 or 4 troops

#### Complete Trait Mapping (All 25 Active Troops)

| Troop | Primary | Secondary | Cost |
|-------|---------|-----------|------|
| archer_queen | Clan | Ranger | 5 |
| bandit | Ace | Assassin | 4 |
| barbarian | Clan | Brawler | 2 |
| dart_goblin | Goblin | Ranger | 3 |
| electro_giant | Giant | Superstar | 3 |
| executioner | Ace | Thrower | 3 |
| goblin | Goblin | Assassin | 2 |
| goblin_machine | Goblin | Brutalist | 4 |
| golden_knight | Noble | Assassin | 5 |
| mega_knight | Ace | Brawler | 4 |
| mini_pekka | P.E.K.K.A | Brutalist | 2 |
| monk | Ace | Superstar | 5 |
| musketeer | Clan | Superstar | 3 |
| pekka | P.E.K.K.A | Brawler | 3 |
| prince | Noble | Brawler | 3 |
| princess | Noble | Blaster | 4 |
| royal_ghost | Undead | Assassin | 4 |
| royal_giant | Giant | Ranger | 2 |
| skeleton | Undead | (Spawned) | 0 |
| skeleton_dragon | Undead | Ranger | 2 |
| skeleton_king | Undead | Brutalist | 5 |
| spear_goblin | Goblin | Thrower | 2 |
| valkyrie | Clan | Brutalist | 3 |
| witch | Undead | Superstar | 4 |
| wizard | Clan | Blaster | 2 |

#### How Trait Counting Works

The system automatically parses traits from troop counts and includes them in the state vector.

**Key: Counts UNIQUE TROOP TYPES per trait, not total troops.**

Example:
1. **CV provides troop counts**: `{"bandit": 5, "dart_goblin": 3, "spear_goblin": 2}`
2. **System looks up traits**:
   - bandit → Ace + Assassin
   - dart_goblin → Goblin + Ranger
   - spear_goblin → Goblin + Thrower
3. **System counts UNIQUE troop types per trait**:
   - Ace: 1 (1 troop type: bandit)
   - Goblin: 2 (2 troop types: dart_goblin, spear_goblin)
   - Assassin: 1 (1 troop type: bandit)
   - Ranger: 1 (1 troop type: dart_goblin)
   - Thrower: 1 (1 troop type: spear_goblin)
4. **System normalizes**: Divide by max trait count (5)
   - Ace: 1/5 = 0.20
   - Goblin: 2/5 = 0.40
   - Assassin: 1/5 = 0.20
   - Ranger: 1/5 = 0.20
   - Thrower: 1/5 = 0.20
5. **Appended to state**: 14 trait features (indices 101-114)

The agent learns trait diversity (e.g., "I have 2 troop types with Goblin trait, buying another Goblin troop gives me 3 types = stronger activation!").

See `rl/troop_traits.py` for implementation.

### State Example
```python
state = [
    # Agent's troop counts - NORMALIZED (indices 0-24, ACTIVE TROOPS ONLY)
    0/27,   # archer_queen: 0 → 0.0
    0/27,   # bandit: 0 → 0.0
    1/27,   # barbarian: 1 → 0.037
    3/27,   # dart_goblin: 3 on battlefield → 0.111
    # ... (21 more normalized troop counts for active troops)

    # Current elixir - NORMALIZED (index 25)
    0.35,  # e.g., 35 elixir with max=100 → 0.35

    # Card Slot 1 - ONE-HOT (indices 26-50): dart_goblin (index 3)
    0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,

    # Card Slot 2 - ONE-HOT (indices 51-75): golden_knight (index 8)
    0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,

    # Card Slot 3 - ONE-HOT (indices 76-100): prince (index 14)
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,
]
```

**Costs for this example** (looked up from ACTIVE_TROOP_COSTS):
- Slot 1 (dart_goblin, index 3): 3 elixir
- Slot 2 (golden_knight, index 8): 5 elixir
- Slot 3 (prince, index 14): 3 elixir

---

## Design Rationale

This section explains **why** we made each major design choice, backed by research and practical considerations.

### 1. One-Hot Encoding for Card Slots

**Choice**: Each of 3 card slots encoded as 24-dimensional one-hot vector (72 features total, active troops only)

**Alternatives considered**:
- Integer IDs (0-23): 3 features
- Learned embeddings: ~24 features (3 slots × 8D embeddings)

**Why one-hot**:
- ✅ **No false ordering**: Integer encoding implies false troop hierarchy, which is meaningless
- ✅ **Standard for categorical data**: Industry best practice for discrete categories
- ✅ **Fast learning**: Network doesn't waste capacity learning troop relationships from scratch
- ✅ **Interpretable**: Can directly see which troop is in which slot
- ✅ **Small overhead**: 111 features is still tiny for modern neural networks
- ✅ **Proven in card games**: Similar to representations in Hearthstone AI research
- ✅ **Only active troops**: Excludes rotated out troops and skeleton spawned unit, keeps state focused

**Trade-off**: Larger state vector (111 vs ~43), but computational cost is negligible

### 2. Action Masking for Invalid Actions

**Choice**: Mask unaffordable actions by setting Q-values to `-inf` during selection

**Alternatives considered**:
- Negative rewards (-100) for invalid purchases
- No special handling (let environment reject)
- Penalty-based learning

**Why action masking**:
- ✅ **Research-backed**: Huang & Ontañón (2020) proved this gives valid gradient updates
- ✅ **Efficiency**: Prevents wasting 30-50% of experiences on learning affordability rules
- ✅ **Faster convergence**: Agent focuses 100% on strategic decisions
- ✅ **Guarantees valid play**: Physically impossible to take invalid actions
- ✅ **Standard practice**: Used in AlphaGo, OpenAI Five, Hearthstone bots
- ✅ **Off-policy friendly**: MDPI (2023) showed this works well with DQN-like algorithms

**Supporting evidence**: "The naive policy gradient is indeed a valid gradient that optimizes both the masked policy and original policy concurrently" (MDPI 2023)

### 3. Static Cost Lookup Table

**Choice**: Store troop costs in `TROOP_COSTS` dict, not in state vector

**Alternatives considered**:
- Include costs as 3 features (indices 30-32)
- Learn costs from experience

**Why static lookup**:
- ✅ **Costs never change**: Game constants don't need to be learned
- ✅ **Simpler state**: 105 features instead of 108
- ✅ **Separation of concerns**: State = observations, costs = game rules
- ✅ **Easier debugging**: Can verify costs match game mechanics
- ✅ **Faster action masking**: Direct lookup vs decoding from state

**Principle**: Don't make the agent learn what you already know

### 4. Two-Level Reward Structure

**Choice**: Intermediate rewards (±10 per round) + macro rewards (±100 for placement)

**Alternatives considered**:
- Sparse rewards (only final placement)
- Dense rewards (every action)
- Win/loss only (binary)

**Why two-level**:
- ✅ **Frequent feedback**: Round rewards every 30-60 seconds prevent sparse reward problem
- ✅ **Strategic emphasis**: Match rewards 10x larger emphasize final goal
- ✅ **Credit assignment**: Easier to trace round wins to recent purchases
- ✅ **Balanced exploration**: Short-term + long-term incentives
- ✅ **Proven in CCGs**: Hearthstone RL agents use similar multi-objective rewards

**Tuning rationale**:
- Round rewards: ±10 (significant but not overwhelming)
- Match rewards: ±100 (1st place) to -100 (8th place)
- Ratio: 10:1 ensures final placement matters most

### 5. DQN Architecture (256-256-128-4)

**Choice**: 4-layer fully-connected network with ReLU activations

**Alternatives considered**:
- Shallow network (2 layers)
- Wider network (512+ neurons)
- Different architectures (dueling, LSTM)

**Why this architecture**:
- ✅ **Handles 111 inputs**: First layer (256) is ~2.3x input size (standard rule of thumb)
- ✅ **Deep enough**: 4 layers can learn complex troop synergies and trait patterns
- ✅ **Not too deep**: Avoid vanishing gradients and overfitting
- ✅ **Proven capacity**: Similar architectures work in Atari DQN (Mnih 2015)
- ✅ **Fast training**: ~195K parameters trains quickly on CPU/GPU

**Future upgrades**:
- Dueling DQN: Separate value/advantage streams (Wang et al. 2015)
- Double DQN: Reduces Q-value overestimation (van Hasselt 2015)

### 6. Normalized State Features [0, 1]

**Choice**: All features scaled to 0-1 range

**Why normalization**:
- ✅ **Equal gradient contribution**: Prevents elixir (0-100) from dominating troop counts (0-27)
- ✅ **Faster convergence**: Standard practice in deep learning (2-3x faster training)
- ✅ **Stable learning**: Prevents gradient explosion from large values
- ✅ **Better weight initialization**: Xavier/He initialization assumes normalized inputs
- ✅ **Transfer learning**: Easier to fine-tune or swap network architectures

**Specific choices**:
- Troop counts: `min(count, 27) / 27` (clips outliers, normalizes to [0,1])
- Elixir: `min(elixir, MAX) / MAX` or log scaling (pending user input)
- Card slots: One-hot {0,1} (inherently normalized)

### 7. Deploy Phase Timing Only

**Choice**: Agent makes decisions only during deploy phase, until elixir depleted or "do nothing"

**Alternatives considered**:
- Continuous decision-making during battle
- Fixed purchase schedule (every N seconds)
- Battle phase troop deployment decisions

**Why deploy phase only**:
- ✅ **Natural decision point**: Deploy phase is when purchases happen in game
- ✅ **Simplified problem**: Focusing on purchases first, deployment later
- ✅ **Clear episodes**: Each deploy phase is a clear decision sequence
- ✅ **Matches game flow**: Real players also make purchases during this phase
- ✅ **Easier data collection**: No need to track battle phase actions yet

**Future extension**: Battle phase deployment (troop placement, targeting) as separate RL task

### 8. Experience Replay Buffer

**Choice**: Store 100K experiences, sample random minibatches of 64

**Why experience replay**:
- ✅ **Breaks correlation**: Random sampling prevents sequential bias
- ✅ **Data efficiency**: Reuse experiences multiple times
- ✅ **Stabilizes training**: Reduces variance in gradient updates
- ✅ **Core DQN innovation**: Mnih et al. (2015) showed this is critical for convergence
- ✅ **Proven capacity**: 100K experiences ~= 500-1000 matches of data

**Buffer size rationale**:
- Too small (1K): Forgets old strategies too quickly
- Too large (1M): Memory intensive, stale data
- 100K: Balances memory, diversity, and recency

### 9. Discrete Action Space (4 Actions)

**Choice**: Purchase slot 1, 2, 3, or do nothing

**Alternatives considered**:
- Continuous actions (purchase amount, timing)
- Hierarchical actions (buy/upgrade, which slot)
- All troop types as actions (26-action space)

**Why 4 discrete actions**:
- ✅ **Matches game mechanics**: You can only buy what's in the shop
- ✅ **Small action space**: DQN excels at discrete actions
- ✅ **Encodes card identity in state**: Agent learns "buy dart_goblin" not "buy slot 1"
- ✅ **Generalizes across shops**: Same action works regardless of slot contents
- ✅ **Natural stopping condition**: "Do nothing" signals end of purchases

**Key insight**: By encoding **which troop** is in each slot (via one-hot), the agent learns strategic value of troops, not positional bias

### 10. Track Purchased Troops (Not Deployed Positions)

**Choice**: State includes count of each troop type owned, not battlefield positions

**Alternatives considered**:
- 2D grid of battlefield with troop positions
- Troop coordinates (x, y) for each unit
- CNN on battlefield image

**Why counts only**:
- ✅ **Simpler state**: 30 features vs thousands (grid) or variable length (coordinates)
- ✅ **Position-invariant**: "I have 5 archers" matters more than exact locations during deploy
- ✅ **Easier CV integration**: Computer vision already counts troops by type
- ✅ **Deploy phase focus**: Positions matter in battle, but we're optimizing purchases
- ✅ **Proven sufficient**: Card game AIs (Hearthstone) succeed without spatial info

**Future extension**: Battle phase agent could use spatial CNN on battlefield

### 11. Epsilon-Greedy Exploration

**Choice**: Start ε=1.0, decay to ε=0.1 over training

**Why epsilon-greedy**:
- ✅ **Simple and effective**: Standard exploration for DQN
- ✅ **Ensures exploration**: Early random actions discover strategies
- ✅ **Converges to exploitation**: Late training uses learned policy
- ✅ **Proven in practice**: Atari DQN, AlphaGo bootstrap all use ε-greedy
- ✅ **Works with action masking**: Sample random valid action, not random invalid

**Decay schedule**: `ε = max(0.1, ε * 0.995)` after each episode
- Reaches 0.1 after ~900 episodes (reasonable for convergence)

---

## Addressing Affordability: Action Masking

### The Problem
**How do we prevent the agent from attempting to purchase cards it cannot afford?**

### Recommended Solution: Action Masking
Implement **action masking** to restrict the agent to only valid (affordable) actions:

```python
def get_valid_actions(state_vector):
    """
    Returns a boolean mask of valid actions based on current elixir.

    Args:
        state_vector: Normalized state vector (111 features)

    Returns:
        valid_actions: [bool, bool, bool, bool] for actions [0, 1, 2, 3]
    """
    # Denormalize elixir (assuming PRACTICAL_MAX_ELIXIR normalization)
    normalized_elixir = state_vector[24]
    current_elixir = normalized_elixir * PRACTICAL_MAX_ELIXIR

    # Decode one-hot slots to troop IDs (ACTIVE TROOPS ONLY - 24 troops)
    slot_1_onehot = state_vector[25:49]   # Indices 25-48
    slot_2_onehot = state_vector[49:73]   # Indices 49-72
    slot_3_onehot = state_vector[73:97]   # Indices 73-96

    slot_1_id = np.argmax(slot_1_onehot)
    slot_2_id = np.argmax(slot_2_onehot)
    slot_3_id = np.argmax(slot_3_onehot)

    # Look up costs from static table
    cost_1 = TROOP_COSTS[slot_1_id]
    cost_2 = TROOP_COSTS[slot_2_id]
    cost_3 = TROOP_COSTS[slot_3_id]

    # Check affordability
    valid_actions = [
        current_elixir >= cost_1,  # Can afford slot 1?
        current_elixir >= cost_2,  # Can afford slot 2?
        current_elixir >= cost_3,  # Can afford slot 3?
        True                       # Can always do nothing
    ]

    return valid_actions
```

### Why Action Masking?
1. **Efficiency**: Prevents wasted experiences on invalid actions
2. **Faster Learning**: Agent only explores meaningful action space
3. **Guarantees Valid Play**: Physically prevents illegal moves
4. **Standard Practice**: Used in most RL systems with dynamic action spaces (e.g., AlphaGo, poker bots)

### Implementation in DQN
During action selection (both training and inference):

```python
def select_action(state, epsilon):
    valid_actions = get_valid_actions(state)

    if random.random() < epsilon:
        # Random action from valid set
        valid_indices = [i for i, valid in enumerate(valid_actions) if valid]
        action = random.choice(valid_indices)
    else:
        # Greedy action from valid set
        q_values = model(state)
        q_values[~valid_actions] = -float('inf')  # Mask invalid actions
        action = torch.argmax(q_values)

    return action
```

### Alternative Approaches (Not Recommended)
1. **Negative Reward Penalty**: Give -100 reward for invalid purchases
   - ❌ Wastes training time learning what's invalid
   - ❌ Agent must fail many times to learn affordability

2. **No Special Handling**: Let agent attempt any action
   - ❌ Requires game environment to reject invalid actions
   - ❌ Still wastes experiences

---

## Reward Structure

### Two-Level Reward System

#### 1. Intermediate Rewards (After Each Round)
Rewards given after each round (win or loss) within a match:

```python
def calculate_round_reward(round_result):
    """
    Args:
        round_result: "win" or "loss"

    Returns:
        reward: float
    """
    if round_result == "win":
        return +10.0
    else:  # loss
        return -10.0
```

**Frequency**: Multiple times per match (typically 3-5 rounds per match)

#### 2. Macro Rewards (End of Match)
Rewards based on final placement detected via OCR:

```python
def calculate_match_reward(placement):
    """
    Args:
        placement: int (1-8 typically, 1 = 1st place)

    Returns:
        reward: float
    """
    placement_rewards = {
        1: +100.0,   # 1st place
        2: +50.0,    # 2nd place
        3: +25.0,    # 3rd place
        4: +10.0,    # 4th place
        5: -10.0,    # 5th place
        6: -25.0,    # 6th place
        7: -50.0,    # 7th place
        8: -100.0,   # 8th place
    }

    return placement_rewards.get(placement, 0.0)
```

**Frequency**: Once per match

### Total Episode Reward
```python
total_reward = sum(round_rewards) + match_reward
```

### Reward Design Rationale
- **Round rewards**: Provide frequent feedback, encourage short-term tactical wins
- **Match rewards**: Emphasize overall strategy and final placement
- **Balanced magnitudes**: Match rewards (±100) are ~10x round rewards (±10) to emphasize final performance while still valuing intermediate wins

---

## Training Data Collection

### Autonomous Self-Play
- Bot runs continuously on an **Android emulator**
- Plays full matches, collecting experiences during deploy phases
- No human intervention required

### Experience Collection
Each experience tuple contains:
```python
experience = (state, action, reward, next_state, done)
```

Stored in a **replay buffer** for batch training:
```python
replay_buffer = ReplayBuffer(capacity=100000)
```

### Data Flow
1. Bot observes state from computer vision
2. DQN selects action (with action masking)
3. Action executed in emulator
4. Reward observed (round win/loss or match placement)
5. Next state observed
6. Experience stored in replay buffer
7. DQN trained on random minibatch from buffer

---

## Deep Q-Network Architecture

### Input Layer
- **Input**: State vector (111 features)
- **Normalization**: All features normalized to [0, 1] range (see State Representation)
- **Includes**: 24 active troops + elixir + card slots + trait features

### Hidden Layers (Suggested)
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class DQN(nn.Module):
    def __init__(self, state_size=111, action_size=4):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_size, 256)   # 111 → 256
        self.fc2 = nn.Linear(256, 256)           # 256 → 256
        self.fc3 = nn.Linear(256, 128)           # 256 → 128
        self.fc4 = nn.Linear(128, action_size)   # 128 → 4

    def forward(self, x):
        """
        Args:
            x: State tensor of shape (batch_size, 111)

        Returns:
            Q-values tensor of shape (batch_size, 4)
        """
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        return self.fc4(x)  # Raw Q-values (no activation)
```

**Architecture Rationale**:
- Larger first layer (256) to handle 111 input features
- Deep enough (4 layers) to learn troop synergies, trait patterns, and strategies
- Can be tuned based on training performance

### Output Layer
- **Output**: Q-values for 4 actions [Q(s,a₀), Q(s,a₁), Q(s,a₂), Q(s,a₃)]
- **No activation**: Raw Q-values (can be negative)
- **Action selection**: `action = argmax(Q-values)` after masking invalid actions

---

## Training Algorithm: DQN with Experience Replay

### Hyperparameters (Initial Suggestions)
```python
LEARNING_RATE = 0.001
GAMMA = 0.99              # Discount factor
EPSILON_START = 1.0       # Initial exploration rate
EPSILON_END = 0.1         # Final exploration rate
EPSILON_DECAY = 0.995     # Decay per episode
BATCH_SIZE = 64
REPLAY_BUFFER_SIZE = 100000
TARGET_UPDATE_FREQ = 1000  # Update target network every N steps
```

### Training Loop
```python
for episode in range(num_episodes):
    state = env.reset()  # Start new match
    episode_reward = 0

    while not done:
        # Select action with epsilon-greedy + action masking
        action = select_action(state, epsilon)

        # Execute action
        next_state, reward, done = env.step(action)

        # Store experience
        replay_buffer.push(state, action, reward, next_state, done)

        # Train on minibatch
        if len(replay_buffer) > BATCH_SIZE:
            batch = replay_buffer.sample(BATCH_SIZE)
            loss = train_step(batch)

        state = next_state
        episode_reward += reward

    # Decay epsilon
    epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)

    # Update target network periodically
    if episode % TARGET_UPDATE_FREQ == 0:
        target_net.load_state_dict(policy_net.state_dict())
```

---

## Implementation Roadmap

### Phase 1: State Extraction
- [ ] Create state vector builder from computer vision detections
- [ ] Map card detections to troop type IDs
- [ ] Extract elixir amount from OCR
- [ ] Track purchased troops throughout match

### Phase 2: DQN Model
- [ ] Implement DQN neural network
- [ ] Implement replay buffer
- [ ] Implement action masking logic
- [ ] Implement epsilon-greedy with masking

### Phase 3: Reward System
- [ ] Implement round win/loss detection
- [ ] Implement OCR for final placement detection
- [ ] Calculate and assign rewards

### Phase 4: Training Infrastructure
- [ ] Integrate DQN with bot's deploy phase
- [ ] Create training loop
- [ ] Add logging and metrics (win rate, avg placement, loss curves)
- [ ] Implement model checkpointing

### Phase 5: Evaluation
- [ ] Test trained agent vs baseline (random purchases)
- [ ] Monitor convergence and stability
- [ ] Tune hyperparameters

---

## Open Questions & Future Enhancements

### Current Design Decisions ✓
1. **Active Troops**: 24 unique active troops (excludes 5 rotated out + 1 spawned unit)
   - **Rotated out**: archer, baby_dragon, e_wiz, giant_skeleton, knight
   - **Spawned unit**: skeleton (not purchasable)
2. **Troop Costs**: Fixed costs ranging from 2-5 elixir (verified from mergetacticsbuild.com)
3. **State Normalization**: All features normalized to [0, 1] range
4. **Max Troop Counts**: 27 units per troop type
5. **Card Slot Encoding**: One-hot encoding (3 slots × 24 active troops = 72 features)
6. **Trait Features**: 14 features (7 primary + 7 secondary traits, auto-parsed from troop counts)
7. **Total State Size**: 111 features (24 troops + 1 elixir + 72 card slots + 14 traits)

### Remaining Questions
1. **Elixir Normalization**: What's a typical maximum elixir at deploy phase start?
   - **Need**: To finalize elixir normalization (practical max vs log scaling)
   - **Current placeholder**: PRACTICAL_MAX_ELIXIR = 100

### Future Enhancements

#### State Enhancements
- **Enemy Troop State**: Add enemy troop counts (25 features + 14 trait features = 39 more features)
- **Spatial Information**: Encode battlefield positions (complex, maybe use CNN)
- **Enemy Elixir**: Track opponent's elixir if visible
- **Round Information**: Current round number, rounds won/lost

#### Algorithm Enhancements
- **Double DQN**: Use separate networks for action selection and evaluation
- **Dueling DQN**: Separate value and advantage streams
- **Prioritized Experience Replay**: Sample important experiences more frequently
- **Multi-Step Returns**: Use n-step TD targets instead of 1-step

---

## File Structure (Proposed)

```
rl/
├── rl_design.md              # This file
├── dqn_model.py              # DQN network architecture
├── replay_buffer.py          # Experience replay buffer
├── state_builder.py          # Converts CV detections to state vector
├── reward_calculator.py      # Calculates rewards from game events
├── action_masking.py         # Action masking logic
├── train.py                  # Main training loop
├── config.py                 # Hyperparameters and constants
├── utils.py                  # Helper functions
└── models/                   # Saved model checkpoints
    └── checkpoints/
```

---

## References

### Core Deep Q-Learning Papers
- **[Playing Atari with Deep Reinforcement Learning](https://arxiv.org/abs/1312.5602)** - Mnih et al., 2013
  - *Original DQN paper introducing experience replay and Q-network training*

- **[Human-level control through deep reinforcement learning](https://www.nature.com/articles/nature14236)** - Mnih et al., Nature 2015
  - *Landmark paper showing DQN beating human experts on Atari games*

- **[Deep Reinforcement Learning with Double Q-learning](https://arxiv.org/abs/1509.06461)** - van Hasselt et al., 2015
  - *Fixes Q-value overestimation in DQN (recommended upgrade)*

- **[Dueling Network Architectures for Deep Reinforcement Learning](https://arxiv.org/abs/1511.06581)** - Wang et al., 2015
  - *Separates state value and action advantages (recommended upgrade)*

### Action Masking (Critical for This Project)
- **[A Closer Look at Invalid Action Masking in Policy Gradient Algorithms](https://arxiv.org/abs/2006.14171)** - Huang & Ontañón, 2020
  - *Theoretical justification for masking invalid actions*
  - *Proves action masking gives valid gradient updates*
  - *Code available on GitHub*

- **[Exploring the Use of Invalid Action Masking in RL: RTS Games](https://www.mdpi.com/2076-3417/13/14/8283)** - Applied Sciences, 2023
  - *Compares on-policy vs off-policy algorithms with action masking*
  - *Shows DQN-like methods work well with masking*
  - *Recommends Off-PIAM for general tasks*

- **[Index Advisor via DQN with Invalid Action Mask in Tree-Structured Action Space](https://link.springer.com/chapter/10.1007/978-3-031-22137-8_32)** - 2021
  - *DQN + action masking implementation*
  - *Combines with Double DQN and Dueling DQN*

### Card Game / Strategy Game RL
- **[Applying Reinforcement Learning and Supervised Learning to Play Hearthstone](https://www.researchgate.net/publication/322671813)** - 2017
  - *Breaking large action spaces into smaller parts*
  - *Agents competed with human experts*

- **[Exploring Reinforcement Learning Approaches for Drafting in Collectible Card Games](https://www.sciencedirect.com/science/article/abs/pii/S1875952122000490)** - Cowling et al., 2022
  - *Deep RL for card selection in draft mode*
  - *Agents learned to prefer low-cost cards*
  - *Multi-objective rewards for card games*

- **[Improving Hearthstone AI by Combining MCTS and Neural Nets](https://arxiv.org/pdf/1808.04794)** - 2018
  - *AlphaGo-style approach to card games*

### Implementation References
- **[Hearthstone AI (GitHub)](https://github.com/peter1591/hearthstone-ai)** - MCTS + neural networks in C++
- **[Hearthstone Deep RL (GitHub)](https://github.com/dillondaudert/Hearthstone-AI)** - DQN implementation in Python/TensorFlow

### Background Reading
- **[Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book-2nd.html)** - Sutton & Barto, 2018
  - *Chapters 6-7 (Temporal Difference Learning, DQN)*
