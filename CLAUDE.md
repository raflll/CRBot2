# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
TacticForge is an AI bot for Clash Royale's Merge Fight Tactics mode, combining computer vision, machine learning, and game automation. The system uses real-time screenshot analysis to detect game state and make strategic decisions.

## Development Commands

### Running the Application
```bash
./run.sh                    # Recommended: Auto-setup launcher with venv
python tacticforge.py       # Terminal UI (Textual-based)
python elixirai_cli.py      # CLI interface
```

### Data Collection (Automated)
```bash
python screenshot_collector.py --games 10      # Play 10 games automatically
python screenshot_collector.py --duration 300  # Run for 5 minutes
python screenshot_collector.py --create-config # Create configuration file
```

### Testing
```bash
python test_detection.py    # Test detection systems
python test_ui.py           # Test UI components
```

### YOLO Training
```bash
cd src/vision
python train_yolov11.py     # Train YOLOv11 model on collected dataset
```

## Architecture

### Core Components
- **tacticforge.py**: Main Textual UI application with state management and controls
- **elixirai_cli.py**: CLI alternative with simple console interface
- **screenshot_collector.py**: Fully automated gameplay bot for data collection (plays games autonomously using OCR)
- **src/bot/**: Bot logic, state machine, and strategy implementations
- **src/detection/**: Computer vision pipeline for game state detection (includes GameOverDetector)
- **src/vision/**: YOLO model training scripts and pretrained weights
- **src/config/**: Configuration management and settings
- **data/**: Dataset (train/valid/test) and YOLO configuration
- **docs/**: System design and architecture documentation

### State Machine Hierarchy
The bot uses a hierarchical state machine (src/bot/states/):
- **HomeState**: Main menu navigation
- **DeployState**: Troop deployment phase
- **BattleState**: Active battle management  
- **VictoryState/DefeatState**: Match results handling
- **ErrorState**: Recovery from unknown states

### Detection System
Multi-region detection (src/detection/):
- Troop detection in deploy and battlefield areas
- Shop detection for available units
- Resource tracking (elixir, coins)
- Game state identification

### Configuration
- JSON-based configs in src/config/
- Capture regions, intervals, and screen settings
- Strategy parameters and bot behavior

## Key Development Patterns

### Adding New Detection Features
1. Implement detector in src/detection/
2. Add to DetectionResult dataclass
3. Update state machine to use new data

### Creating New Strategies
1. Inherit from BaseStrategy in src/bot/strategies/
2. Implement required methods (deploy_troops, upgrade_troops)
3. Register in strategy manager

### State Machine Extensions
1. Create new state class inheriting from State
2. Define enter(), execute(), and exit() methods
3. Add transitions in state manager

## Dependencies
- Python 3.10+
- Key packages: opencv-python, pillow, mss, textual, rich, numpy
- ML features: pytorch, ultralytics (YOLOv11)

## Important Notes
- Multi-monitor support with automatic detection
- Screenshots saved with timestamps in data/screenshots/
- Extensive logging in logs/ directory
- Virtual environment automatically managed by run.sh