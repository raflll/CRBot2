# Data Collection System for Merge Fight Tactics

## Overview
An automated system for collecting gameplay screenshots and data from Clash Royale's Merge Fight Tactics mode to create training datasets for computer vision models.

## System Architecture

### 1. Automated Gameplay Bot
A simple bot that plays the game with random actions while capturing screenshots for annotation.

```python
class DataCollectionBot:
    def __init__(self):
        self.screenshot_interval = 1.0  # seconds
        self.action_interval = 2.0      # seconds
        self.session_duration = 3600    # 1 hour sessions
        self.output_directory = "./raw_screenshots"
```

### 2. Core Components

#### Screen Capture Module
```python
def capture_screenshot():
    """
    Captures game screen at regular intervals
    Returns: PIL Image object with timestamp
    """
    - Use PyAutoGUI or MSS for fast capture
    - Add timestamp to filename
    - Save in lossless format (PNG)
    - Log capture metadata
```

#### Random Action Generator
```python
def generate_random_action():
    """
    Generates random game actions for data diversity
    """
    actions = [
        "buy_random_unit",
        "merge_random_units", 
        "wait",
        "use_ability",
        "reroll_shop"
    ]
    return weighted_random_choice(actions)
```

#### Game State Detector
Basic detection to ensure the bot stays in-game:
- Menu detection
- Game over detection
- Error/disconnect handling
- Round transition detection

### 3. Data Collection Pipeline

#### Collection Workflow
```
1. Start Game
   ↓
2. Enter Merge Fight Tactics Mode
   ↓
3. Begin Collection Loop:
   a. Capture screenshot
   b. Perform random action
   c. Wait interval
   d. Check game state
   ↓
4. Handle Game End → Restart
   ↓
5. Continue until session complete
```

#### Screenshot Organization
```
raw_screenshots/
├── session_001/
│   ├── metadata.json
│   ├── 2024_01_15_14_30_00_001.png
│   ├── 2024_01_15_14_30_01_002.png
│   └── ...
├── session_002/
└── ...
```

### 4. Implementation Details

#### Main Collection Script
```python
import time
import random
import pyautogui
import json
from datetime import datetime
from pathlib import Path

class MergeFightDataCollector:
    def __init__(self, config):
        self.config = config
        self.session_id = self.generate_session_id()
        self.screenshot_count = 0
        self.metadata = []
        
    def run_collection_session(self):
        """Main collection loop"""
        self.setup_directories()
        self.start_game()
        
        start_time = time.time()
        while time.time() - start_time < self.config['session_duration']:
            # Capture screenshot
            screenshot = self.capture_game_screen()
            
            # Perform random action
            action = self.perform_random_action()
            
            # Log metadata
            self.log_action_metadata(screenshot, action)
            
            # Check game state
            if self.is_game_over():
                self.handle_game_over()
            
            time.sleep(self.config['capture_interval'])
            
        self.save_session_metadata()
    
    def capture_game_screen(self):
        """Captures and saves screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{self.screenshot_count:04d}.png"
        
        # Define game window region
        game_region = self.config['game_region']  # (x, y, width, height)
        
        # Capture screenshot
        screenshot = pyautogui.screenshot(region=game_region)
        
        # Save screenshot
        filepath = self.session_path / filename
        screenshot.save(filepath)
        
        self.screenshot_count += 1
        return {'filename': filename, 'timestamp': timestamp}
    
    def perform_random_action(self):
        """Executes random game action"""
        action_weights = {
            'buy_unit': 0.3,
            'merge_units': 0.25,
            'wait': 0.2,
            'reroll': 0.15,
            'use_ability': 0.1
        }
        
        action = random.choices(
            list(action_weights.keys()),
            weights=list(action_weights.values())
        )[0]
        
        if action == 'buy_unit':
            self.click_random_shop_unit()
        elif action == 'merge_units':
            self.drag_random_merge()
        elif action == 'reroll':
            self.click_reroll_button()
        elif action == 'use_ability':
            self.click_random_ability()
        # 'wait' does nothing
        
        return action
```

#### Action Implementation
```python
def click_random_shop_unit(self):
    """Clicks random unit in shop"""
    shop_slots = self.config['shop_positions']
    slot = random.choice(shop_slots)
    
    # Add human-like randomness
    x = slot['x'] + random.randint(-5, 5)
    y = slot['y'] + random.randint(-5, 5)
    
    pyautogui.click(x, y)
    time.sleep(random.uniform(0.1, 0.3))

def drag_random_merge(self):
    """Attempts random unit merge"""
    board_positions = self.config['board_positions']
    
    # Select two random positions
    pos1 = random.choice(board_positions)
    pos2 = random.choice(board_positions)
    
    if pos1 != pos2:
        pyautogui.dragTo(
            pos2['x'], pos2['y'],
            duration=random.uniform(0.3, 0.5),
            button='left'
        )
```

### 5. Configuration System

#### config.json
```json
{
    "game_window": {
        "x": 0,
        "y": 0,
        "width": 1920,
        "height": 1080
    },
    "game_region": {
        "x": 100,
        "y": 100,
        "width": 1720,
        "height": 880
    },
    "capture_settings": {
        "interval": 1.0,
        "format": "png",
        "quality": 100
    },
    "action_settings": {
        "min_delay": 0.5,
        "max_delay": 3.0,
        "human_variance": true
    },
    "shop_positions": [
        {"x": 400, "y": 900},
        {"x": 550, "y": 900},
        {"x": 700, "y": 900},
        {"x": 850, "y": 900},
        {"x": 1000, "y": 900}
    ],
    "board_positions": [
        {"x": 400, "y": 600, "slot": "1_1"},
        {"x": 500, "y": 600, "slot": "1_2"},
        {"x": 600, "y": 600, "slot": "1_3"}
    ],
    "session_settings": {
        "duration": 3600,
        "auto_restart": true,
        "restart_delay": 10
    }
}
```

### 6. Metadata Tracking

#### Metadata Structure
```json
{
    "session_id": "20240115_143000_abc123",
    "start_time": "2024-01-15T14:30:00",
    "end_time": "2024-01-15T15:30:00",
    "total_screenshots": 3600,
    "game_sessions": 12,
    "actions_performed": {
        "buy_unit": 324,
        "merge_units": 267,
        "wait": 180,
        "reroll": 152,
        "use_ability": 77
    },
    "screenshots": [
        {
            "filename": "20240115_143000_0001.png",
            "timestamp": "2024-01-15T14:30:00.123",
            "action": "buy_unit",
            "game_state": "battle_phase",
            "round": 1
        }
    ]
}
```

### 7. Data Preprocessing for Roboflow

#### Export Script
```python
def prepare_roboflow_upload():
    """
    Organizes screenshots for Roboflow upload
    """
    # Filter out menu/loading screens
    filtered_images = filter_valid_game_screens()
    
    # Sample diverse dataset
    sampled_images = sample_diverse_images(
        filtered_images,
        sample_size=1000
    )
    
    # Organize by game state
    organized = {
        'early_game': [],
        'mid_game': [],
        'late_game': [],
        'battle_phase': []
    }
    
    # Create upload package
    create_upload_zip(organized)
```

### 8. Quality Assurance

#### Screenshot Validation
- **Blur Detection**: Remove blurry captures
- **Duplicate Detection**: Remove identical frames
- **Transition Filtering**: Remove menu/loading screens
- **Coverage Check**: Ensure variety of game states

```python
def validate_screenshot(image_path):
    """
    Validates screenshot quality
    """
    img = cv2.imread(image_path)
    
    # Check blur
    if calculate_blur_score(img) > threshold:
        return False
    
    # Check if game screen
    if not is_game_screen(img):
        return False
    
    return True
```

### 9. Advanced Features

#### Smart Sampling
```python
def smart_sample_screenshots():
    """
    Intelligently samples diverse screenshots
    """
    criteria = {
        'unit_variety': check_unit_diversity,
        'board_states': check_board_coverage,
        'game_phases': check_phase_distribution,
        'action_types': check_action_coverage
    }
    
    return optimize_sample_selection(criteria)
```

#### Session Recovery
```python
def recover_interrupted_session():
    """
    Resumes data collection after interruption
    """
    last_session = load_last_session()
    if last_session['status'] == 'interrupted':
        resume_from_checkpoint(last_session)
```

### 10. Deployment Setup

#### Requirements
```txt
pyautogui==0.9.54
opencv-python==4.8.1
pillow==10.1.0
mss==9.0.1
numpy==1.24.3
pandas==2.0.3
```

#### Docker Container
```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    python3-tk \
    python3-dev \
    scrot

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "collect_data.py"]
```

### 11. Usage Instructions

#### Basic Usage
```bash
# Start collection with default settings
python collect_data.py

# Custom configuration
python collect_data.py --config custom_config.json

# Specific duration
python collect_data.py --duration 7200

# With preprocessing
python collect_data.py --preprocess --upload-ready
```

#### Monitoring
```bash
# Watch collection progress
python monitor.py --session-id SESSION_ID

# View statistics
python stats.py --input-dir ./raw_screenshots

# Validate dataset
python validate.py --check-quality --remove-duplicates
```

### 12. Roboflow Integration

#### Upload Preparation
1. **Image Selection**: Choose 500-1000 diverse screenshots
2. **Initial Labeling**: Create starter annotations for common units
3. **Class Definition**: Define all unit types and game elements
4. **Augmentation Settings**: Configure appropriate augmentations

#### Annotation Guidelines
- **Bounding Boxes**: Tight boxes around each unit
- **Class Labels**: unit_type_level (e.g., "archer_3")
- **Attributes**: Team (ally/enemy), position, state
- **Special Elements**: Abilities, resources, UI elements

### 13. Troubleshooting

#### Common Issues
1. **Game Detection Fails**
   - Adjust game_region coordinates
   - Update detection templates

2. **Actions Not Registering**
   - Increase action delays
   - Check click coordinates

3. **Memory Issues**
   - Implement batch processing
   - Compress older screenshots

4. **Screenshot Quality**
   - Adjust capture settings
   - Use different capture library

### 14. YouTube Video Data Collection

#### Overview
Scraping YouTube gameplay videos provides access to high-quality gameplay from skilled players, supplementing the random-action data collection.

#### Video Scraping Pipeline
```python
import yt_dlp
import cv2
from pathlib import Path

class YouTubeGameplayExtractor:
    def __init__(self, output_dir="./youtube_frames"):
        self.output_dir = Path(output_dir)
        self.frame_interval = 30  # Extract every 30th frame (1 per second at 30fps)
        
    def download_video(self, url):
        """Downloads YouTube video"""
        ydl_opts = {
            'format': 'best[height<=1080]',
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return self.output_dir / f"{info['title']}.{info['ext']}"
    
    def extract_frames(self, video_path, channel_name):
        """Extract frames from video"""
        cap = cv2.VideoCapture(str(video_path))
        frame_count = 0
        extracted_count = 0
        
        session_dir = self.output_dir / f"{channel_name}_{video_path.stem}"
        session_dir.mkdir(exist_ok=True)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % self.frame_interval == 0:
                # Check if frame is gameplay (not intro/outro)
                if self.is_gameplay_frame(frame):
                    filename = f"frame_{extracted_count:06d}.png"
                    cv2.imwrite(str(session_dir / filename), frame)
                    extracted_count += 1
                    
            frame_count += 1
            
        cap.release()
        return extracted_count
    
    def is_gameplay_frame(self, frame):
        """Detect if frame shows actual gameplay"""
        # Check for UI elements specific to Merge Fight Tactics
        # This would use template matching or simple color detection
        return self.detect_game_ui(frame)
```

#### YouTube Channel Sources
```python
YOUTUBE_SOURCES = {
    "channels": [
        {
            "name": "ClashRoyaleOfficial",
            "playlist": "PLxxxxxMergeFightTactics",
            "quality": "high"
        },
        {
            "name": "ProPlayer1",
            "search_query": "merge fight tactics gameplay",
            "min_duration": 600  # 10+ minute videos
        }
    ],
    "specific_videos": [
        "https://youtube.com/watch?v=VIDEO_ID_1",
        "https://youtube.com/watch?v=VIDEO_ID_2"
    ]
}
```

#### Automated YouTube Scraping
```python
def batch_process_youtube():
    """Process multiple YouTube videos"""
    extractor = YouTubeGameplayExtractor()
    
    # Search for relevant videos
    search_results = search_youtube(
        query="Clash Royale Merge Fight Tactics gameplay 2024",
        max_results=50
    )
    
    for video in search_results:
        try:
            # Download video
            video_path = extractor.download_video(video['url'])
            
            # Extract frames
            frames = extractor.extract_frames(
                video_path,
                video['channel']
            )
            
            # Clean up video file to save space
            video_path.unlink()
            
            print(f"Extracted {frames} frames from {video['title']}")
            
        except Exception as e:
            print(f"Failed to process {video['url']}: {e}")
```

#### Frame Processing and Filtering
```python
class GameplayFrameFilter:
    def __init__(self):
        self.ui_templates = self.load_ui_templates()
        
    def filter_frames(self, frame_dir):
        """Filter frames to keep only high-quality gameplay"""
        valid_frames = []
        
        for frame_path in frame_dir.glob("*.png"):
            frame = cv2.imread(str(frame_path))
            
            # Check quality criteria
            if all([
                self.is_gameplay_screen(frame),
                self.is_high_quality(frame),
                self.has_clear_units(frame),
                not self.is_transition(frame)
            ]):
                valid_frames.append(frame_path)
                
        return valid_frames
    
    def is_high_quality(self, frame):
        """Check frame quality"""
        # No motion blur
        blur = cv2.Laplacian(frame, cv2.CV_64F).var()
        if blur < 100:
            return False
            
        # Good resolution
        height, width = frame.shape[:2]
        if width < 1280 or height < 720:
            return False
            
        return True
```

#### Advantages of YouTube Data
1. **Expert Gameplay**: Learn from skilled players' strategies
2. **Diverse Scenarios**: Wide variety of game states and strategies
3. **No Setup Required**: No need to run the game
4. **Large Volume**: Thousands of hours of gameplay available
5. **Different Metas**: Videos from different time periods show meta evolution

#### Processing Pipeline Integration
```python
def integrate_youtube_data():
    """Combine YouTube and automated collection data"""
    
    # Process YouTube frames
    youtube_frames = process_youtube_batch()
    
    # Process automated collection
    auto_frames = process_automated_collection()
    
    # Combine datasets
    combined_dataset = {
        'youtube': {
            'frames': youtube_frames,
            'weight': 0.6  # Higher weight for expert play
        },
        'automated': {
            'frames': auto_frames,
            'weight': 0.4
        }
    }
    
    # Balance dataset
    balanced = balance_dataset(combined_dataset)
    
    # Prepare for annotation
    prepare_roboflow_upload(balanced)
```

### 15. Optimization Tips

1. **Performance**
   - Use MSS for faster capture
   - Implement multi-threading
   - Optimize image compression
   - Batch process YouTube videos overnight

2. **Storage**
   - Implement rolling deletion
   - Use cloud storage
   - Compress completed sessions
   - Delete source videos after frame extraction

3. **Accuracy**
   - Calibrate click positions
   - Add position verification
   - Implement feedback loops
   - Cross-validate YouTube and automated data