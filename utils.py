"""
Utility functions and helper scripts
"""

import cv2
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Utils")


def test_rtsp_connection(rtsp_url: str) -> bool:
    """
    Test RTSP connection without relying on external tools.
    
    Args:
        rtsp_url (str): RTSP URL to test
    
    Returns:
        bool: True if connection successful
    """
    logger.info(f"Testing RTSP connection: {rtsp_url}")
    
    try:
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            logger.info(f"✓ RTSP connection successful: {frame.shape}")
            return True
        else:
            logger.error("✗ Failed to read frame from RTSP stream")
            return False
    
    except Exception as e:
        logger.error(f"✗ RTSP connection error: {e}")
        return False


def test_camera_device(device_index: int = 0) -> bool:
    """
    Test local camera device.
    
    Args:
        device_index (int): Camera device index
    
    Returns:
        bool: True if camera works
    """
    logger.info(f"Testing camera device {device_index}...")
    
    try:
        cap = cv2.VideoCapture(device_index)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            logger.info(f"✓ Camera working: {frame.shape}")
            return True
        else:
            logger.error("✗ Camera not responding")
            return False
    
    except Exception as e:
        logger.error(f"✗ Camera error: {e}")
        return False


def check_dependencies() -> bool:
    """
    Verify all required dependencies are installed.
    
    Returns:
        bool: True if all dependencies present
    """
    logger.info("Checking dependencies...")
    
    required = {
        "cv2": "opencv-python",
        "torch": "torch",
        "ultralytics": "ultralytics",
        "numpy": "numpy",
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module)
            logger.info(f"✓ {module}")
        except ImportError:
            logger.warning(f"✗ {module} (install: pip install {package})")
            missing.append(package)
    
    if missing:
        logger.error(f"\nMissing dependencies: {', '.join(missing)}")
        logger.info("Install with: pip install " + " ".join(missing))
        return False
    
    logger.info("✓ All dependencies installed")
    return True


def check_gpu() -> dict:
    """
    Check GPU availability and CUDA info.
    
    Returns:
        dict: GPU information
    """
    logger.info("Checking GPU...")
    
    try:
        import torch
        
        info = {
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "current_device": None,
            "device_name": None,
            "cuda_version": torch.version.cuda,
        }
        
        if torch.cuda.is_available():
            info["current_device"] = torch.cuda.current_device()
            info["device_name"] = torch.cuda.get_device_name(0)
            logger.info(f"✓ GPU Available: {info['device_name']}")
        else:
            logger.info("ℹ GPU Not Available (will use CPU)")
        
        return info
    
    except Exception as e:
        logger.error(f"GPU check failed: {e}")
        return {"cuda_available": False, "error": str(e)}


def benchmark_model(model_name: str = "yolov8n.pt") -> dict:
    """
    Run quick benchmark on YOLOv8 model.
    
    Args:
        model_name (str): Model to benchmark
    
    Returns:
        dict: Benchmark results
    """
    logger.info(f"Benchmarking model: {model_name}")
    
    try:
        from ultralytics import YOLO
        import numpy as np
        import time
        
        # Load model
        model = YOLO(model_name)
        
        # Create dummy image
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Warmup
        model(dummy_img, verbose=False)
        
        # Benchmark
        times = []
        num_runs = 10
        
        for _ in range(num_runs):
            start = time.time()
            model(dummy_img, verbose=False)
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        fps = 1 / avg_time
        
        results = {
            "model": model_name,
            "avg_inference_ms": avg_time * 1000,
            "fps": fps,
            "min_ms": min(times) * 1000,
            "max_ms": max(times) * 1000,
        }
        
        logger.info(f"✓ Benchmark complete: {fps:.1f} FPS ({avg_time*1000:.1f}ms avg)")
        
        return results
    
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return {"error": str(e)}


def download_model(model_name: str = "yolov8n.pt") -> bool:
    """
    Pre-download YOLOv8 model.
    
    Args:
        model_name (str): Model to download
    
    Returns:
        bool: True if successful
    """
    logger.info(f"Downloading model: {model_name}")
    
    try:
        from ultralytics import YOLO
        YOLO(model_name)
        logger.info(f"✓ Model downloaded: {model_name}")
        return True
    
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False


def system_diagnostics():
    """Run complete system diagnostics."""
    logger.info("\n" + "="*60)
    logger.info("DRONE DROP DETECTION - SYSTEM DIAGNOSTICS")
    logger.info("="*60 + "\n")
    
    # Check dependencies
    deps_ok = check_dependencies()
    logger.info()
    
    # Check GPU
    gpu_info = check_gpu()
    logger.info()
    
    # Quick benchmarks if everything is available
    if deps_ok:
        logger.info("Running benchmarks (this may take ~30 seconds)...\n")
        
        for model in ["yolov8n.pt", "yolov8s.pt"]:
            try:
                bench = benchmark_model(model)
                logger.info()
            except:
                logger.info(f"Skipping {model} benchmark\n")
    
    logger.info("="*60)
    logger.info("DIAGNOSTICS COMPLETE")
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Utility functions")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--check-gpu", action="store_true", help="Check GPU")
    parser.add_argument("--test-camera", action="store_true", help="Test camera device")
    parser.add_argument("--test-rtsp", type=str, help="Test RTSP URL")
    parser.add_argument("--benchmark", type=str, default="yolov8n.pt", help="Benchmark model")
    parser.add_argument("--download-model", type=str, help="Download model")
    parser.add_argument("--diagnostics", action="store_true", help="Full diagnostics")
    
    args = parser.parse_args()
    
    if args.check_deps:
        check_dependencies()
    elif args.check_gpu:
        import json
        print(json.dumps(check_gpu(), indent=2))
    elif args.test_camera:
        test_camera_device()
    elif args.test_rtsp:
        test_rtsp_connection(args.test_rtsp)
    elif args.benchmark:
        import json
        print(json.dumps(benchmark_model(args.benchmark), indent=2))
    elif args.download_model:
        download_model(args.download_model)
    elif args.diagnostics:
        system_diagnostics()
    else:
        parser.print_help()
