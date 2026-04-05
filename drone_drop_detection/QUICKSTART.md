# QUICK START GUIDE

## Installation (2-5 minutes)

### Linux / macOS

```bash
# 1. Run installation script
chmod +x install.sh
./install.sh

# 2. Test setup
python utils.py --diagnostics

# 3. Try demo
python main.py --use-demo
```

### Windows

```cmd
# 1. Run installation script
install.bat

# 2. Test setup
python utils.py --diagnostics

# 3. Try demo
python main.py --use-demo
```

---

## What You'll See

When running the demo, you'll see:

```
╔═══════════════════════════════════════════════════════════╗
║   🚁 DRONE DROP ZONE DETECTION SYSTEM 🚁                  ║
║                                                            ║
║   AI-Powered Safe Zone Identification                     ║
║   Real-Time Video Analysis with YOLOv8                   ║
╚═══════════════════════════════════════════════════════════╝

============================================================
🚁 DRONE DROP ZONE DETECTION SYSTEM INITIALIZED
============================================================

📡 Step 1: Initializing Camera Connection...
Using synthetic demo video
Created synthetic demo video...
✓ Synthetic demo video created: demo_video.mp4
✓ Camera initialized: 640x480 @ 30.0 FPS

🤖 Step 2: Loading YOLOv8 Model...
✓ GPU detected, using CUDA
✓ Model loaded successfully on cuda

🎯 Step 3: Initializing Safe Zone Analyzer...
✓ Safe zone analyzer initialized

...
```

A video window will open showing:
- 🟢 **Green zones** = Safe for drops
- 🔴 **Red zones** = Unsafe (people/obstacles)
- Detection bounding boxes with confidence scores
- FPS counter and threat analysis panel

---

## Connection to Real Drone

1. **Connect to drone Wi-Fi**:
   ```bash
   # Connect to "WIFI_UFO_40828c" or your drone's network
   ```

2. **Verify connection**:
   ```bash
   python utils.py --test-rtsp rtsp://192.168.1.1:7070/webcam
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Optional: Save video for analysis**:
   ```bash
   python main.py --save-video
   # Output saved to: output/drone_drop_detection_*.mp4
   ```

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'ultralytics'"

**Solution**:
```bash
# Rerun installation
python -m pip install -r requirements.txt --upgrade
```

### Problem: RTSP connection fails

**Solution**:
```bash
# Check connection is working
python utils.py --test-rtsp rtsp://192.168.1.1:7070/webcam

# If that fails:
# 1. Verify drone Wi-Fi connection
# 2. Check IP address is correct
# 3. Try with VLC player: vlc rtsp://192.168.1.1:7070/webcam
```

### Problem: Very slow FPS (1-2 FPS)

**Solution**:
Edit `config/config.py`:
```python
YOLO_MODEL = "yolov8n.pt"  # Use nano model instead
USE_GPU = True              # Enable GPU if available
```

### Problem: "CUDA out of memory"

**Solution**:
```bash
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
python main.py
```

---

## Keyboard Controls While Running

| Key | Action |
|-----|--------|
| `q` | Quit |
| `s` | Save current frame as JPEG |
| `p` | Pause/Resume |

---

## Next Steps

1. **Customize detection criteria** → Edit `config/config.py`
2. **Integrate with drone control** → Add commands in `main.py`
3. **Deploy to edge device** → Use `--headless` mode
4. **Build mobile app** → Create REST API wrapper

---

## Performance Tips

- **Faster inference**: Use `yolov8n.pt` instead of larger models
- **Better accuracy**: Use `yolov8m.pt` with GPU
- **Lower latency**: Run in headless mode (`--headless`)
- **GPU acceleration**: Install CUDA PyTorch version during setup

---

## Support

For detailed information:
- See `README.md` for full documentation
- Check source code comments in `src/` modules
- Run `python utils.py --diagnostics` for system info
- Review config options in `config/config.py`

---

**Happy drone monitoring! 🚁🎯**
