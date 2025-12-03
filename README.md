# Merge Fight Tactics Bot (TacticForge)

A Python-based AI bot for playing Clash Royale's Merge Fight Tactics mode using computer vision and deep learning.

## Quick Start

### Launch the Terminal UI
```bash
# Method 1: Use the launcher script (recommended)
./run.sh

# Method 2: Direct Python execution
source .venv/bin/activate
python tacticforge.py
```

## Terminal UI Features
- 📸 **Data Collection**: Automated screenshot capture with configurable intervals
- 🧠 **Model Training**: Train YOLO models on collected data
- 🤖 **Bot Control**: Start/stop the bot and monitor performance
- 📊 **Statistics**: View collection and performance metrics
- ⚙️ **Settings**: Configure bot parameters

## Keyboard Shortcuts
- `D` - Data Collection
- `T` - Training
- `B` - Bot Control
- `Q` - Quit
- `ESC` - Go back

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Automated Data Collection

The screenshot collector **plays the game automatically** using OCR detection and collects training data.

#### Basic Usage
```bash
# Play 10 games automatically (recommended)
python screenshot_collector.py --games 10

# Run for 5 minutes
python screenshot_collector.py --duration 300

# Create a config file to customize settings
python screenshot_collector.py --create-config

# Run with custom config
python screenshot_collector.py --config auto_collector_config.json
```

#### Command Line Options
- `--games`: Number of games to play automatically
- `--duration`: Collection time in seconds
- `--output`: Custom output directory
- `--config`: Path to JSON config file

### 3. Automated Collection Features
- **Autonomous gameplay**: Bot plays games from start to finish
- **OCR-based detection**: Uses GameOverDetector to detect game end
- **Random actions**: Simulates human-like gameplay with random choices (1, 2, 3 keys)
- **Auto-restart**: Automatically clicks "Play Again" and starts new games
- **Metadata tracking**: Saves screenshots and actions for each game
- **Session management**: Organized by unique session IDs

## Project Structure
```
CRBot/
├── screenshot_collector.py      # Automated gameplay bot for data collection
├── docs/                        # Documentation
│   ├── merge_fight_tactics_system_design.md  # System architecture
│   └── data_collection_system.md    # Data collection documentation
├── data/                        # Dataset and configuration
│   ├── data.yaml               # YOLO dataset config
│   ├── train/                  # Training images
│   ├── valid/                  # Validation images
│   └── test/                   # Test images
├── src/                         # Source code
│   ├── bot/                    # Bot logic and random actions
│   ├── detection/              # Detection systems (GameOverDetector, etc.)
│   └── vision/                 # YOLO training scripts
├── requirements.txt             # Python dependencies
└── screenshots/                 # Collected screenshots (auto-created)
    └── session_*/              # Individual sessions
        ├── screenshot_*.png    # Screenshots
        └── metadata.json       # Session metadata
```

## Configuration

Create an `auto_collector_config.json` file:
```json
{
  "output_directory": "./screenshots",
  "games_per_session": 10,
  "session_duration": 1800,
  "capture_interval": {
    "min": 30.0,
    "max": 35.0
  },
  "monitor_index": 1,
  "random_actions": {
    "enabled": true,
    "count": 3,
    "delay_between_actions": 1.0
  },
  "end_game_detection": {
    "enabled": true,
    "method": "ocr",
    "timeout_seconds": 200
  }
}
```

## Usage Tips

1. **Start the game** and get to the main menu
2. **Let the bot run autonomously** - it will play games automatically
3. **Don't touch the keyboard/mouse** while the collector is running
4. **Monitor the console** to see game progress and OCR detection
5. **Check metadata.json** after collection to verify captures

## Next Steps

After collecting screenshots:
1. Upload to Roboflow for annotation
2. Label troops, traits, and game elements
3. Train YOLO model on annotated data
4. Implement game state detection
5. Build decision-making system

## Documentation

- [System Design](docs/merge_fight_tactics_system_design.md) - Complete bot architecture
- [Data Collection](docs/data_collection_system.md) - Detailed data pipeline
- [State Machine Architecture](docs/elixirai_state_machine_architecture.md) - Bot state machine design