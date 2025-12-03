# Merge Fight Tactics Bot System Design

## Overview
An intelligent bot system for playing Clash Royale's Merge Fight Tactics mode using computer vision for game state detection and deep learning for strategic decision-making.

## System Architecture

### 1. Computer Vision Module (Game State Detection)
#### YOLO Model Implementation
- **Purpose**: Real-time detection and classification of game elements
- **Detection Targets**:
  - Troops in arena (type, level, position, traits)
  - Troops in reserve (type, level)
  - Shop offerings (troop type, cost)
  - Ruler HP and status
  - Elixir count
  - Game phase (deploy/battle)
  - Enemy troop compositions

#### Image Processing Pipeline
1. Screen capture at 10-30 FPS
2. Preprocessing (resize, normalize)
3. YOLO inference
4. Post-processing (NMS, confidence filtering)
5. State representation conversion

### 2. Game State Representation
```python
GameState = {
    "deploy_phase": {
        "arena": [[troop_type, level, position]],  # Deployed troops
        "reserve": [[troop_type, level]],          # Troops in reserve
        "shop": [[troop_type, level, cost]]        # Available in shop
    },
    "ruler": {
        "hp": int,
        "passive_ability": str
    },
    "elixir": int,
    "round_number": int,
    "phase": "deploy" | "battle",
    "enemy_states": [...]  # Similar structure for each opponent
}
```

### 3. Game Simulation Engine
#### Core Components
- **Troop Database**: Stats for each Clash Royale unit and merged versions
- **Trait System**: Track trait combinations and bonuses
- **Battle Simulator**: Predicts combat outcomes based on troops
- **Merge Logic**: Track mergeable troops and resulting upgrades
- **Elixir Management**: Track elixir gains from merges

#### Simulation Process
1. Parse current game state (deploy vs battle phase)
2. Generate possible actions:
   - **Deploy Phase**: Buy from shop, merge matching troops, move between arena/reserve
   - **Battle Phase**: Buy/sell between reserve and shop only
3. Simulate battle outcomes based on troop compositions
4. Calculate damage (enemy troops remaining + 1, damage dealt = your troops + ruler)
5. Return optimal action to minimize damage taken

### 4. Decision-Making AI
#### Phase 1: Rule-Based System
- Hard-coded strategies for early development
- Priority system for actions:
  1. Merge matching troops for stronger units
  2. Buy troops that match existing ones for merge potential
  3. Optimize trait combinations for bonuses
  4. Position strongest troops in arena during deploy phase
  5. Manage elixir efficiently (4 base + merge bonuses)

#### Phase 2: Deep Learning Model
##### Architecture Options
1. **Reinforcement Learning (PPO/A3C)**
   - Input: Game state representation
   - Output: Action probabilities
   - Reward: Win/loss, damage dealt/taken

2. **Supervised Learning (Transformer/CNN)**
   - Input: Game state + opponent history
   - Output: Best action prediction
   - Training: Human expert games

##### Model Features
- Attention mechanism for opponent board analysis
- Temporal awareness (previous rounds)
- Meta-game adaptation

### 5. Action Execution Module
#### Screen Interaction
- **Library Options**: PyAutoGUI, ADB (for mobile)
- **Action Types**:
  - Click (buy troop from shop)
  - Drag (merge matching troops or move between arena/reserve)
  - Refresh (get new shop offerings by purchasing)
- **Timing**: Respect phase restrictions (deploy vs battle)

#### Action Queue System
```python
ActionQueue = [
    {"type": "buy", "troop": "archer", "shop_slot": 2},
    {"type": "merge", "from": (x1, y1), "to": (x2, y2)},
    {"type": "move_to_arena", "troop": "knight", "from_reserve": 1},
    {"type": "move_to_reserve", "from_arena": (x, y)}
]
```

## Technical Stack

### Core Technologies (Python-based)
- **Programming Language**: Python 3.10+
- **Computer Vision**: YOLOv8 (Ultralytics), OpenCV-Python
- **Deep Learning**: PyTorch (primary), TensorFlow as alternative
- **Game Automation**: PyAutoGUI, MSS (for screenshots), ADB (for mobile)
- **Data Management**: SQLite (local), PostgreSQL (production)
- **API Framework**: FastAPI (for distributed training)
- **Image Processing**: Pillow, scikit-image
- **Numerical Computing**: NumPy, Pandas

### Development Tools
- **Annotation**: Roboflow, LabelImg
- **Monitoring**: Weights & Biases, TensorBoard
- **Version Control**: Git, DVC (for datasets)

## Training Pipeline

### 1. Data Collection Phase
- Automated gameplay recording
- Manual annotation in Roboflow
- Dataset versioning and augmentation

### 2. Computer Vision Training
- Transfer learning from COCO pretrained models
- Custom dataset fine-tuning
- Validation on live gameplay

### 3. Strategy Model Training
#### Reinforcement Learning Approach
1. Self-play in simulated environment
2. Curriculum learning (easy → hard opponents)
3. Population-based training for diversity

#### Supervised Learning Approach
1. Collect high-level player replays
2. Extract state-action pairs
3. Train with behavioral cloning
4. Fine-tune with self-play

## Performance Metrics

### Computer Vision Metrics
- mAP (mean Average Precision) > 0.9
- Inference time < 50ms
- Troop detection accuracy
- Phase detection accuracy

### Strategy Metrics
- Win rate (last ruler standing)
- Average damage taken per round
- Merge efficiency (successful merges per round)
- Trait combo utilization
- Elixir management efficiency

## Challenges and Solutions

### 1. Real-time Performance
**Challenge**: Processing speed for quick decisions
**Solution**: 
- Model quantization
- GPU acceleration
- Predictive caching

### 2. Game Updates
**Challenge**: New units, balance changes
**Solution**:
- Modular architecture
- Continuous learning pipeline
- Version-specific models

### 3. Trait System Complexity
**Challenge**: Understanding and optimizing trait combinations
**Solution**:
- Build comprehensive trait database
- Track successful trait combos from expert play
- Learn trait synergies through gameplay analysis

### 4. Phase-Specific Actions
**Challenge**: Different actions allowed in deploy vs battle phase
**Solution**:
- Robust phase detection
- Action validation based on current phase
- Separate strategies for each phase

## Development Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [ ] Set up development environment
- [ ] Implement basic screen capture
- [ ] Create initial YOLO training dataset
- [ ] Build simple rule-based player

### Phase 2: Computer Vision (Weeks 5-8)
- [ ] Train YOLO model for unit detection
- [ ] Implement real-time inference pipeline
- [ ] Validate detection accuracy
- [ ] Optimize performance

### Phase 3: Game Logic (Weeks 9-12)
- [ ] Build game simulation engine
- [ ] Implement battle outcome prediction
- [ ] Create action execution system
- [ ] Test end-to-end gameplay

### Phase 4: AI Development (Weeks 13-20)
- [ ] Design neural network architecture
- [ ] Implement training pipeline
- [ ] Collect training data
- [ ] Train and evaluate models

### Phase 5: Optimization (Weeks 21-24)
- [ ] Performance tuning
- [ ] Strategy refinement
- [ ] Testing against various opponents
- [ ] Documentation and deployment

## Future Enhancements

1. **Multi-game Support**: Extend to other auto-battler games
2. **Cloud Deployment**: Distributed bot network
3. **Learning from Streams**: Real-time learning from Twitch/YouTube
4. **Coaching Mode**: Suggest moves to human players
5. **Meta Analysis**: Track and predict meta shifts