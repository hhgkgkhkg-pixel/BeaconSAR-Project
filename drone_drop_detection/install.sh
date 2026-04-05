#!/bin/bash
# Installation script for Drone Drop Detection System

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Drone Drop Detection System - Installation Script       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "📍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📍 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

echo ""
echo "📍 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

echo "✓ Using Python: $(which python)"
echo ""

# Upgrade pip
echo "📍 Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1 || true
echo "✓ Pip upgraded"
echo ""

# Check for GPU
echo "📍 Checking for GPU support..."
cuda_available=$(python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "False")

if [ "$cuda_available" = "True" ]; then
    echo "✓ GPU detected! Installing CUDA-accelerated PyTorch..."
    cuda_version=$(python -c "import torch; print(torch.version.cuda)" 2>/dev/null || echo "11.8")
    echo "  Using CUDA $cuda_version"
    
    # Try to install CUDA version
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 > /dev/null 2>&1 || {
        echo "  ⚠️  GPU install failed, falling back to CPU"
    }
else
    echo "ℹ️  GPU not detected, using CPU (slower inference)"
fi
echo ""

# Install requirements
echo "📍 Installing dependencies from requirements.txt..."
python -m pip install -q -r requirements.txt

echo "✓ Dependencies installed"
echo ""

# Download YOLOv8 models
echo "📍 Downloading YOLOv8 models (this may take a minute)..."
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>&1 | grep -q "model" && echo "✓ YOLOv8 models downloaded" || true
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ Installation Complete!                               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "  1. Test your setup:"
echo "     python utils.py --diagnostics"
echo ""
echo "  2. Try the demo:"
echo "     python main.py --use-demo"
echo ""
echo "  3. Connect to drone and run:"
echo "     python main.py"
echo ""
echo "For more information, see README.md"
echo ""
