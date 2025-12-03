#!/usr/bin/env python3
"""
YOLOv11 Training Script for TacticForge
Trains object detection model for Clash Royale troops and cards
"""

from ultralytics import YOLO
import torch
from pathlib import Path

def main():
    # Get project root directory (2 levels up from this script)
    project_root = Path(__file__).parent.parent.parent
    # Check if CUDA is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    # Load pretrained YOLOv11 model
    # Options: yolo11n.pt (nano), yolo11s.pt (small), yolo11m.pt (medium),
    #          yolo11l.pt (large), yolo11x.pt (xlarge)
    model = YOLO('yolo11n.pt')  # Start with nano for faster training

    print("\nStarting YOLOv11 training...")
    print("Dataset: 53 classes (troops + cards)")
    print("Train: 85 images | Valid: 18 images | Test: 8 images\n")

    # Train the model
    results = model.train(
        data=str(project_root / 'data' / 'data.yaml'),           # Path to dataset config
        epochs=100,                 # Number of training epochs
        imgsz=640,                  # Image size (640x640)
        batch=16,                   # Batch size (adjust based on GPU memory)
        device=device,              # Device to use
        project=str(project_root / 'runs' / 'detect'),      # Project directory
        name='tacticforge_yolo11',  # Experiment name

        # Performance settings
        patience=20,                # Early stopping patience
        save=True,                  # Save checkpoints
        save_period=10,             # Save every N epochs

        # Data augmentation (automatic in YOLOv11)
        hsv_h=0.015,               # Hue augmentation
        hsv_s=0.7,                 # Saturation augmentation
        hsv_v=0.4,                 # Value augmentation
        degrees=0.0,               # Rotation augmentation (0-180)
        translate=0.1,             # Translation augmentation
        scale=0.5,                 # Scaling augmentation
        shear=0.0,                 # Shear augmentation
        perspective=0.0,           # Perspective augmentation
        flipud=0.0,                # Vertical flip probability
        fliplr=0.5,                # Horizontal flip probability
        mosaic=1.0,                # Mosaic augmentation probability
        mixup=0.0,                 # Mixup augmentation probability

        # Optimization
        optimizer='auto',          # Auto-select optimizer
        lr0=0.01,                  # Initial learning rate
        lrf=0.01,                  # Final learning rate factor
        momentum=0.937,            # SGD momentum
        weight_decay=0.0005,       # Weight decay
        warmup_epochs=3.0,         # Warmup epochs
        warmup_momentum=0.8,       # Warmup momentum

        # Visualization
        plots=True,                # Save training plots
        verbose=True,              # Verbose output
    )

    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_results = model.val(data=str(project_root / 'data' / 'data.yaml'), split='test')

    # Export model
    print("\nExporting model...")
    model.export(format='onnx')  # Export to ONNX for deployment

    weights_dir = project_root / 'runs' / 'detect' / 'tacticforge_yolo11' / 'weights'
    print("\n" + "="*60)
    print("Training complete!")
    print(f"Best weights: {weights_dir / 'best.pt'}")
    print(f"Last weights: {weights_dir / 'last.pt'}")
    print("="*60)

if __name__ == "__main__":
    main()
