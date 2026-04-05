@echo off
REM Installation script for Drone Drop Detection System (Windows)

setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  Drone Drop Detection System - Installation Script       ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM Check Python version
echo 📍 Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✓ Python %python_version%
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo 📍 Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment exists
)

echo.
echo 📍 Activating virtual environment...
call venv\Scripts\activate.bat

echo ✓ Using Python: %python%
echo.

REM Upgrade pip
echo 📍 Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
echo ✓ Pip upgraded
echo.

REM Install dependencies
echo 📍 Installing dependencies from requirements.txt...
python -m pip install -q -r requirements.txt

if errorlevel 1 (
    echo ❌ Installation failed!
    pause
    exit /b 1
)

echo ✓ Dependencies installed
echo.

REM Download YOLOv8 model
echo 📍 Downloading YOLOv8 models (this may take a minute)...
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>&1 | find "model" >nul && (
    echo ✓ YOLOv8 models downloaded
) || (
    echo ⚠️  Model download may have issues, but installation can continue
)

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║  ✅ Installation Complete!                               ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo Next steps:
echo.
echo   1. Test your setup:
echo      python utils.py --diagnostics
echo.
echo   2. Try the demo:
echo      python main.py --use-demo
echo.
echo   3. Connect to drone and run:
echo      python main.py
echo.
echo For more information, see README.md
echo.

pause
