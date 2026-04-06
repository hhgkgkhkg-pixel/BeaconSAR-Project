# Dockerfile for Drone Drop Detection System
# Build: docker build -t drone-drop-detection .
# Run:   docker run --gpus all -v $(pwd)/output:/app/output drone-drop-detection

FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Copy project files
COPY requirements.txt .
COPY config/ config/
COPY src/ src/
COPY main.py .
COPY utils.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download YOLOv8 model
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Create output directory
RUN mkdir -p output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=1

# Default command
CMD ["python3", "main.py", "--use-demo"]

# Alternative commands:
# docker run ... drone-drop-detection python3 main.py           # Live feed
# docker run ... drone-drop-detection python3 main.py --save-video  # Record
# docker run ... drone-drop-detection python3 utils.py --diagnostics
