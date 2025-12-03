# Merge Fight Tactics Bot (TacticForge)

A Python-based AI bot for playing Clash Royale's Merge Fight Tactics mode using computer vision and deep learning.

## Quick Start

### Launch the Terminal UI
```bash
# Method 1: Use the launcher script
./run.sh

# Method 2: Direct Python execution
source .venv/bin/activate
python tacticforge.py

# Method 3: Use the executable
./tacticforge
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

### 2. Collect Screenshots for Dataset

#### Basic Usage
```bash
# Run for 5 minutes with default settings
python screenshot_collector.py --duration 300

# Create a config file to customize settings
python screenshot_collector.py --create-config

# Run with custom config
python screenshot_collector.py --config screenshot_config.json
```

#### Command Line Options
- `--duration`: Collection time in seconds
- `--interval`: Fixed screenshot interval (disables randomization)
- `--output`: Custom output directory
- `--config`: Path to JSON config file

### 3. Screenshot Collection Features
- **Random intervals**: Captures at randomized intervals (1-3 seconds default)
- **Metadata tracking**: Automatically saves metadata for each screenshot
- **Session management**: Organized by unique session IDs
- **Configurable regions**: Capture full screen or specific game window

## Project Structure
```
CRBot/
├── screenshot_collector.py      # Data collection script
├── merge_fight_tactics_system_design.md  # System architecture
├── data_collection_system.md    # Data collection documentation
├── requirements.txt             # Python dependencies
├── screenshots/                 # Collected screenshots (auto-created)
│   └── session_*/              # Individual sessions
│       ├── screenshot_*.png    # Screenshots
│       └── metadata.json       # Session metadata
└── screenshot_config.json      # Configuration (optional)
```

## Configuration

Create a `screenshot_config.json` file:
```json
{
  "output_directory": "./screenshots",
  "capture_interval": {
    "min": 1.0,
    "max": 3.0
  },
  "session_duration": 300,
  "capture_region": {
    "x": 100,
    "y": 100,
    "width": 1720,
    "height": 880
  },
  "monitor_index": 1,
  "image_format": "png"
}
```

## Usage Tips

1. **Start the game** before running the collector
2. **Position the game window** consistently for better data
3. **Play normally** while the collector runs in the background
4. **Check metadata.json** after collection to verify captures

## Next Steps

After collecting screenshots:
1. Upload to Roboflow for annotation
2. Label troops, traits, and game elements
3. Train YOLO model on annotated data
4. Implement game state detection
5. Build decision-making system

## Documentation

- [System Design](merge_fight_tactics_system_design.md) - Complete bot architecture
- [Data Collection](data_collection_system.md) - Detailed data pipeline