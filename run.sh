#!/bin/bash
# TacticForge Bot Launcher Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🎮 TacticForge Bot 🎮        ║${NC}"
echo -e "${GREEN}║  Merge Fight Tactics AI System   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════╝${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import textual" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r requirements.txt
fi

# Run the TUI application
echo -e "${GREEN}Starting TacticForge Terminal UI...${NC}"
python tacticforge.py

# Deactivate virtual environment on exit
deactivate