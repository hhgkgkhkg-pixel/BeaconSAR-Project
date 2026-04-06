# 🚁 Drone Drop Zone Detection System

**AI-Powered Real-Time Detection of Safe Sensor Drop Zones**

An intelligent Python application that uses YOLOv8 object detection to analyze live drone video feeds and identify safe zones for deploying rescue sensors.

## Features ✨

- **Real-Time Video Analysis**: Captures and processes RTSP drone feeds at 5-10+ FPS
- **YOLOv8 Object Detection**: Detects people, obstacles, and open areas
- **Safe Zone Identification**: 
  - 🟢 Green zones mark safe areas (no people, low obstacles)
  - 🔴 Red zones mark unsafe areas (human presence or hazards)
  - Safety confidence scoring
- **Visual Overlay System**:
  - Bounding boxes for all detections
  - Heatmap showing safety scores
  - Real-time threat analysis
  - FPS and performance metrics
- **Offline Operation**: Fully functional without internet
- **Modular Architecture**: Easy to extend and modify detection logic
- **Optional Video Recording**: Save annotated video for review
- **Keyboard Controls**: Live frame capture, pause, and quit commands

## System Architecture 🏗️

```
.
├── main.py                 # Entry point
├── config/
│   ├── __init__.py
│   └── config.py          # Configuration parameters
├── src/
│   ├── __init__.py
│   ├── camera.py          # RTSP video capture
│   ├── detection.py       # YOLOv8 object detection
│   ├── safe_zones.py      # Safe zone analysis logic
│   └── visualization.py   # Frame annotation & display
├── output/                # Video output directory
├── docs/                  # Project documentation
├── notebooks/             # Jupyter notebooks for experimentation
├── test_system.py         # System tests
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── setup.py               # Package setup
├── Dockerfile             # Docker configuration
└── README.md              # This file
```

## Requirements 📋

- **Python**: 3.10 or higher
- **GPU** (optional): NVIDIA GPU with CUDA support for faster inference
- **Drone**: RC UFO or similar with RTSP video feed
- **Network**: Direct Wi-Fi connection to drone

### Hardware Recommendations

- **Minimum**: CPU with 4GB RAM, ~100MB disk space
- **Recommended**: GPU (NVIDIA), 8GB+ RAM for smooth 30 FPS operation

## Installation 🔧

### 1. Clone Repository

```bash
git clone https://github.com/hhgkgkhkg-pixel/BeaconSAR-Project.git
cd BeaconSAR-Project
```

### 2. Create Python Virtual Environment (Recommended)

```bash
# Using venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n drone python=3.10
conda activate drone
```

### 3. Install Dependencies

```bash
# CPU-only version (slower inference)
pip install -r requirements.txt

# OR GPU-accelerated version (NVIDIA CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt

# OR GPU-accelerated version (NVIDIA CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import cv2; import torch; from ultralytics import YOLO; print('✓ All imports successful')"
```

> Windows users can run the bundled installer script from the project root:
>
> ```bat
> install.bat rtsp://192.168.1.1:7070/webcam
> ```
>
> This creates the virtual environment, installs dependencies, updates `config/config.py` with your drone RTSP URL, and launches `main.py`.

### 5. Run Tests (Optional)

```bash
# Quick sanity tests
python test_system.py --quick

# Full test suite
python test_system.py --full
```

## Quick Start 🚀

### Demo Mode (No Drone Required)

Test the system with synthetic video:

```bash
python main.py --use-demo --save-video
```

This will:
- Generate synthetic video with obstacles and people
- Run detection and safe zone analysis
- Display annotated video
- Save output to `output/` directory

### Live Drone Feed

Connect to your drone's Wi-Fi and run:

```bash
# Basic real-time monitoring
python main.py

# Save annotated video for later review
python main.py --save-video

# Headless mode (no display, useful for servers)
python main.py --headless

# Combined options
python main.py --save-video --headless &
```

## Keyboard Controls ⌨️

While running (display mode):

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `s` | Save current frame as JPEG |
| `p` | Pause/Resume video |

## Documentation 📖

Additional documentation is available in the `docs/` folder:

- [00_READ_ME_FIRST.txt](docs/00_READ_ME_FIRST.txt) - Quick start guide
- [QUICKSTART.md](docs/QUICKSTART.md) - Quick reference
- [PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) - Project overview
- [DELIVERY.md](docs/DELIVERY.md) - Delivery checklist
- [FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md) - Detailed file structure
- [START_HERE.txt](docs/START_HERE.txt) - Getting started

## Configuration 🎛️

Edit `config/config.py` to customize:

```python
# Drone Connection
DRONE_WIFI_SSID = "WIFI_UFO_40828c"
DRONE_RTSP_URL = "rtsp://192.168.1.1:7070/webcam"

# AI Detection
YOLO_MODEL = "yolov8n.pt"  # nano, small, medium, large, xlarge
YOLO_CONFIDENCE_THRESHOLD = 0.5

# Safe Zone Criteria
SAFE_ZONE_CONFIG = {
    "max_person_confidence": 0.3,
    "min_obstacle_distance": 2.0,
    "open_area_threshold": 0.4,
    "grid_cell_size": 50,
}

# Display
DISPLAY_FRAMERATE = 30
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720

# Video Output
SAVE_VIDEO = True
OUTPUT_VIDEO_FPS = 20
```

### Model Selection

- `yolov8n.pt` - Nano (fastest, ~5-10 FPS on CPU)
- `yolov8s.pt` - Small (better accuracy, ~3-5 FPS on CPU)
- `yolov8m.pt` - Medium (good balance, ~1-3 FPS on CPU)
- `yolov8l.pt` - Large (high accuracy, slower)
- `yolov8x.pt` - XLarge (best accuracy, slowest)

**Recommendation**: Start with `yolov8n.pt` for real-time performance.

## Module Documentation 📚

### Camera Module (`src/camera.py`)

Handles RTSP video capture:

```python
from src.camera import CameraCapture

camera = CameraCapture("rtsp://192.168.1.1:7070/webcam")
camera.connect()
camera.start_capture()

success, frame = camera.read_frame()
camera.stop_capture()
```

**Key Methods**:
- `connect()` - Establish RTSP connection with retry logic
- `start_capture()` - Begin frame capture (threaded)
- `read_frame()` - Get latest frame from queue
- `stop_capture()` - Shutdown and cleanup

### Detection Module (`src/detection.py`)

YOLOv8-based object detection:

```python
from src.detection import create_detector

detector = create_detector("yolov8n.pt", conf_threshold=0.5)
detections = detector.detect(frame)

# Get detections by class
people = detector.get_detections_by_class(detections, "person")
```

**Detected Classes**:
- `person` - Human detection
- `bicycle`, `car`, `motorcycle`, `bus`, `truck` - Vehicles
- `potted plant` - Vegetation/obstacles
- [50+ COCO dataset classes available]

### Safe Zones Module (`src/safe_zones.py`)

Identifies and analyzes safe drop zones:

```python
from src.safe_zones import create_safe_zone_analyzer

analyzer = create_safe_zone_analyzer(640, 480)
analysis = analyzer.analyze_detections(detections)

# Get results
safe_zones = analysis["safe_zones"]
unsafe_zones = analysis["unsafe_zones"]
best_zone = analyzer.get_best_drop_zone(safe_zones)
```

**Output Structure**:
```python
{
    "safe_zones": [
        {
            "center": (x, y),
            "bounds": (x1, y1, x2, y2),
            "confidence": 0.85,
            "area": 50000,
        },
        ...
    ],
    "threat_summary": {
        "people_detected": True,
        "open_area_ratio": 0.6,
        "obstacle_density": 0.4,
    }
}
```

### Visualization Module (`src/visualization.py`)

Creates annotated frames with overlays:

```python
from src.visualization import FrameAnnotator

annotator = FrameAnnotator(640, 480)
annotated = annotator.annotate_frame(
    frame,
    detections,
    safe_zones_analysis,
    show_confidence=True,
    show_fps=25.0,
)
```

## Performance 📊

Typical performance on various hardware:

| Hardware | Model | FPS | Inference Time |
|----------|-------|-----|-----------------|
| Intel i5 CPU | yolov8n | 6-8 | 120-150ms |
| Intel i7 CPU | yolov8n | 8-12 | 80-130ms |
| NVIDIA GTX1080 | yolov8n | 40+ | 20-30ms |
| NVIDIA RTX3080 | yolov8s | 80+ | 12-15ms |

**Notes**:
- First run downloads model (~50MB for nano)
- CPU mode: Use nano or small models
- GPU mode: Can use larger models for better accuracy

## Troubleshooting 🔧

### Connection Issues

```bash
# Test RTSP connection
ffprobe rtsp://192.168.1.1:7070/webcam

# Or try with VLC
vlc rtsp://192.168.1.1:7070/webcam
```

### Slow Performance

1. Use smaller YOLOv8 model (`yolov8n.pt`)
2. Enable GPU acceleration (if available)
3. Reduce `DISPLAY_FRAMERATE` in config
4. Run in headless mode (`--headless`)

### Memory Issues

```bash
# Limit memory usage
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
python main.py
```

### No Detections

1. Verify YOLO model is downloaded (~50MB+)
2. Check video feed is working (`ffprobe`)
3. Lower `YOLO_CONFIDENCE_THRESHOLD` in config
4. Try different model size

## Advanced Usage 🎓

### Custom Detection Classes

Edit `config/config.py`:

```python
DETECT_CLASSES = {
    "person": 0,
    "cat": 15,
    "dog": 16,
    # Add your classes here
}
```

### Safe Zone Criteria

Adjust detection thresholds:

```python
SAFE_ZONE_CONFIG = {
    "max_person_confidence": 0.5,      # Higher = stricter
    "min_obstacle_distance": 3.0,      # Higher = more clearance
    "open_area_threshold": 0.5,        # Higher = more area needed
    "grid_cell_size": 25,              # Smaller = more resolution
}
```

### Custom Detection Logic

Modify `src/safe_zones.py` `_mark_unsafe_zone()` method:

```python
def _mark_unsafe_zone(self, box, threat_type, confidence):
    # Implement custom logic here
    # Example: weighted threat calculation
    threat_weight = {
        "person": 2.0,
        "obstacle": 1.5,
    }
    weight = threat_weight.get(threat_type, 1.0)
    # ... rest of implementation
```

## Future Extensions 🔮

Possible enhancements:

1. **Autonomous Control**: Send commands to drone via Wi-Fi
2. **Mobile App**: Flask/Android UI for remote monitoring
3. **Multi-Drone Support**: Track multiple drones simultaneously
4. **ML Model Training**: Fine-tune detection on custom datasets
5. **Sensor Integration**: Connect with altitude/IMU sensors
6. **Cloud Logging**: Send data to remote server/database
7. **Advanced Analytics**: Generate drop zone reports and statistics
8. **Alert System**: Email/SMS notifications for threats

## API Reference 📖

### Main Application Class

```python
from main import DroneDropDetectionApp

app = DroneDropDetectionApp(
    use_demo=False,
    save_video=True,
    headless=False,
)
app.run()
```

### Component Factory Functions

```python
from src.camera import create_camera_connection
from src.detection import create_detector
from src.safe_zones import create_safe_zone_analyzer

camera = create_camera_connection("rtsp://url")
detector = create_detector("yolov8n.pt")
analyzer = create_safe_zone_analyzer(640, 480)
```

## License 📄

[Add your license here]

## Contributing 🤝

Contributions welcome! Areas for improvement:
- Better obstacle distance calculations
- Improved real-time performance
- Additional detection models support
- Multi-threaded processing pipeline

## Support 💬

For issues or questions:
1. Check troubleshooting section above
2. Review detailed comments in source files
3. Check configuration parameters
4. Enable verbose logging in modules

## References 📚

- [YOLOv8 Documentation](https://docs.ultralytics.com/models/yolov8/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [COCO Dataset](https://cocodataset.org/)

---

**Happy Drop Detecting! 🚁✨**
