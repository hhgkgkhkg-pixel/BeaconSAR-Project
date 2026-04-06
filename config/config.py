# Configuration file for drone drop detection system

# RTSP Feed Configuration
DRONE_WIFI_SSID = "WIFI_UFO_40828c"
DRONE_RTSP_URL = "rtsp://192.168.1.1:7070/webcam"
FALLBACK_TEST_VIDEO = "test_video.mp4"  # For testing without drone

# YOLOv8 Model Configuration
YOLO_MODEL = "yolov8n.pt"  # nano model for speed; use yolov8s.pt, yolov8m.pt for accuracy
YOLO_CONFIDENCE_THRESHOLD = 0.5
YOLO_IOU_THRESHOLD = 0.4

# Detection Classes of Interest
DETECT_CLASSES = {
    "person": 0,          # Class ID for person in COCO dataset
    "bicycle": 1,
    "car": 2,
    "motorcycle": 3,
    "bus": 5,
    "truck": 7,
    "potted plant": 58,   # Trees/plants
    "backpack": 24,
}

# Safe Zone Detection Criteria
SAFE_ZONE_CONFIG = {
    "max_person_confidence": 0.3,      # If person detected above this, zone is unsafe
    "min_obstacle_distance": 2.0,      # Minimum distance in arbitrary units from obstacles
    "open_area_threshold": 0.4,        # Threshold for considering area "open" (0-1)
    "grid_cell_size": 50,              # Size of grid cells for zone analysis (pixels)
}

# Display Configuration
DISPLAY_FRAMERATE = 30  # Target display FPS
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
SHOW_CONFIDENCE_SCORES = True
SHOW_FPS = True

# Video Output Configuration
SAVE_VIDEO = True
OUTPUT_VIDEO_CODEC = "mp4v"
OUTPUT_VIDEO_FPS = 20
OUTPUT_VIDEO_DIR = "./output/"

# Performance Configuration
USE_GPU = True  # Use GPU for inference if available
INFERENCE_FPS_TARGET = 10  # Minimum inference FPS
BATCH_SIZE = 1

# Safe Zone Color Configuration (BGR format for OpenCV)
COLOR_SAFE = (0, 255, 0)      # Green
COLOR_UNSAFE = (0, 0, 255)    # Red
COLOR_DETECTION_BOX = (255, 0, 0)  # Blue
COLOR_GRID = (100, 100, 100)  # Gray

# Text Configuration
FONT = 2  # OpenCV font
FONT_SCALE = 0.6
FONT_COLOR = (255, 255, 255)  # White
THICKNESS = 2
