@echo off
REM Installation script for Drone Drop Detection System (Windows)

setlocal enabledelayedexpansion

REM Default RTSP URL for the drone feed
set "RTSP_URL=rtsp://192.168.1.1:7070/webcam"
if not "%~1"=="" set "RTSP_URL=%~1"

echo.
echo Drone Drop Detection System - Installer
echo.
echo Using RTSP feed: %RTSP_URL%
echo.

REM Check Python version
echo Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Python %python_version%
echo.

REM Create virtual environment if needed
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created
) else (
    echo Virtual environment exists
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Activated virtual environment
echo.

echo Upgrading pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
if errorlevel 1 (
    echo pip upgrade failed, continuing with existing pip
) else (
    echo pip upgraded
)

echo.
echo Installing dependencies from requirements.txt...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
)

echo Dependencies installed
echo.

echo Writing drone RTSP URL into config/config.py...
python -c "from pathlib import Path; import re; path=Path('config/config.py'); text=path.read_text(); text=re.sub(r'^DRONE_RTSP_URL\\s*=.*$', 'DRONE_RTSP_URL = \"%RTSP_URL%\"', text, flags=re.MULTILINE); path.write_text(text)"
if errorlevel 1 (
    echo Failed to update config/config.py
    pause
    exit /b 1
)

echo RTSP URL set in config/config.py
echo.

echo Downloading YOLOv8 model if needed...
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" >nul 2>&1 || (
    echo Model download failed or was already present
)

echo.
echo Installation complete.
echo.
echo Running the app now with your drone RTSP feed...
echo.
python main.py
if errorlevel 1 (
    echo.
    echo The app exited with an error. Please check the output above.
    pause
    exit /b 1
)

echo.
echo The app completed successfully or exited cleanly.
echo.
pause
