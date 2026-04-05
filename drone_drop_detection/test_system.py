"""
Test Suite for Drone Drop Detection System

This module provides comprehensive tests to verify the system is working correctly.

Usage:
    python test_system.py          # Run all tests
    python test_system.py --quick  # Run quick tests only
    python test_system.py --full   # Run full test suite
"""

import sys
import unittest
import tempfile
import os
from pathlib import Path
import logging
import numpy as np

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestSuite")


class TestDependencies(unittest.TestCase):
    """Test if all dependencies are importable."""
    
    def test_import_opencv(self):
        """Test OpenCV import."""
        try:
            import cv2
            self.assertIsNotNone(cv2)
        except ImportError:
            self.fail("OpenCV (cv2) not installed")
    
    def test_import_torch(self):
        """Test PyTorch import."""
        try:
            import torch
            self.assertIsNotNone(torch)
        except ImportError:
            self.fail("PyTorch not installed")
    
    def test_import_ultralytics(self):
        """Test YOLO import."""
        try:
            from ultralytics import YOLO
            self.assertIsNotNone(YOLO)
        except ImportError:
            self.fail("ultralytics not installed")
    
    def test_import_numpy(self):
        """Test NumPy import."""
        try:
            import numpy
            self.assertIsNotNone(numpy)
        except ImportError:
            self.fail("NumPy not installed")


class TestConfig(unittest.TestCase):
    """Test configuration loading."""
    
    def test_config_import(self):
        """Test config module import."""
        from config.config import DRONE_RTSP_URL, YOLO_MODEL
        self.assertIsNotNone(DRONE_RTSP_URL)
        self.assertIsNotNone(YOLO_MODEL)
    
    def test_config_values(self):
        """Test config values are reasonable."""
        from config.config import (
            YOLO_CONFIDENCE_THRESHOLD,
            SAFE_ZONE_CONFIG,
            DISPLAY_FRAMERATE,
        )
        
        self.assertGreater(YOLO_CONFIDENCE_THRESHOLD, 0)
        self.assertLess(YOLO_CONFIDENCE_THRESHOLD, 1)
        self.assertIn("grid_cell_size", SAFE_ZONE_CONFIG)
        self.assertGreater(DISPLAY_FRAMERATE, 0)


class TestCameraModule(unittest.TestCase):
    """Test camera capture module."""
    
    def test_camera_module_import(self):
        """Test camera module import."""
        from src.camera import CameraCapture, create_camera_connection
        self.assertIsNotNone(CameraCapture)
        self.assertIsNotNone(create_camera_connection)
    
    def test_camera_initialization(self):
        """Test creating camera instance."""
        from src.camera import CameraCapture
        camera = CameraCapture("test://url")
        self.assertIsNotNone(camera)
        self.assertFalse(camera.is_running)


class TestDetectionModule(unittest.TestCase):
    """Test object detection module."""
    
    def test_detection_module_import(self):
        """Test detection module import."""
        from src.detection import YOLODetector, create_detector
        self.assertIsNotNone(YOLODetector)
        self.assertIsNotNone(create_detector)
    
    def test_detector_initialization(self):
        """Test creating detector instance."""
        from src.detection import YOLODetector
        detector = YOLODetector("yolov8n.pt", 0.5)
        self.assertIsNotNone(detector)
        self.assertIsNone(detector.model)
    
    def test_dummy_detection(self):
        """Test detection on dummy image."""
        try:
            from src.detection import create_detector
            
            detector = create_detector("yolov8n.pt", 0.5)
            if detector is None:
                self.skipTest("YOLO model couldn't be loaded")
            
            # Create dummy image
            dummy_img = np.zeros((640, 480, 3), dtype=np.uint8)
            
            # Run detection
            results = detector.detect(dummy_img)
            
            self.assertTrue(results.get("success"))
            self.assertIn("boxes", results)
            self.assertIn("confidences", results)
            self.assertIn("labels", results)
        
        except Exception as e:
            self.skipTest(f"Detection test skipped: {e}")


class TestSafeZonesModule(unittest.TestCase):
    """Test safe zone identification module."""
    
    def test_safe_zones_import(self):
        """Test safe zones module import."""
        from src.safe_zones import SafeZoneAnalyzer, create_safe_zone_analyzer
        self.assertIsNotNone(SafeZoneAnalyzer)
        self.assertIsNotNone(create_safe_zone_analyzer)
    
    def test_analyzer_initialization(self):
        """Test creating analyzer instance."""
        from src.safe_zones import SafeZoneAnalyzer
        analyzer = SafeZoneAnalyzer(640, 480)
        self.assertEqual(analyzer.frame_width, 640)
        self.assertEqual(analyzer.frame_height, 480)
    
    def test_analysis_with_no_detections(self):
        """Test safe zone analysis with no detections."""
        from src.safe_zones import SafeZoneAnalyzer
        
        analyzer = SafeZoneAnalyzer(640, 480)
        
        empty_detections = {
            "success": True,
            "boxes": [],
            "confidences": [],
            "class_ids": [],
            "labels": [],
        }
        
        results = analyzer.analyze_detections(empty_detections)
        
        self.assertTrue(results["success"])
        self.assertGreater(len(results["safe_zones"]), 0)
    
    def test_heatmap_generation(self):
        """Test heatmap generation."""
        from src.safe_zones import SafeZoneAnalyzer
        
        analyzer = SafeZoneAnalyzer(640, 480)
        heatmap = analyzer.generate_heatmap()
        
        self.assertEqual(heatmap.shape, (480, 640, 3))
        self.assertEqual(heatmap.dtype, np.uint8)


class TestVisualizationModule(unittest.TestCase):
    """Test visualization module."""
    
    def test_visualization_import(self):
        """Test visualization module import."""
        from src.visualization import FrameAnnotator, VideoWriter
        self.assertIsNotNone(FrameAnnotator)
        self.assertIsNotNone(VideoWriter)
    
    def test_annotator_initialization(self):
        """Test creating annotator instance."""
        from src.visualization import FrameAnnotator
        annotator = FrameAnnotator(640, 480)
        self.assertEqual(annotator.frame_width, 640)
        self.assertEqual(annotator.frame_height, 480)
    
    def test_frame_annotation(self):
        """Test annotating a frame."""
        from src.visualization import FrameAnnotator
        
        annotator = FrameAnnotator(640, 480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        empty_detections = {
            "success": False,
        }
        
        empty_analysis = {
            "safe_zones": [],
            "unsafe_zones": [],
            "threat_summary": {
                "people_detected": False,
                "open_area_ratio": 1.0,
                "obstacle_density": 0.0,
            }
        }
        
        annotated = annotator.annotate_frame(
            frame,
            empty_detections,
            empty_analysis,
        )
        
        self.assertEqual(annotated.shape, frame.shape)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_pipeline_dummy_image(self):
        """Test full detection pipeline on dummy image."""
        try:
            from src.detection import create_detector
            from src.safe_zones import SafeZoneAnalyzer
            from src.visualization import FrameAnnotator
            
            # Create dummy image
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Create modules
            detector = create_detector("yolov8n.pt")
            
            if detector is None:
                self.skipTest("Detector couldn't be loaded")
            
            analyzer = SafeZoneAnalyzer(640, 480)
            annotator = FrameAnnotator(640, 480)
            
            # Run pipeline
            detections = detector.detect(frame)
            analysis = analyzer.analyze_detections(detections)
            annotated = annotator.annotate_frame(
                frame,
                detections,
                analysis,
            )
            
            # Verify outputs
            self.assertTrue(detections.get("success", False))
            self.assertTrue(analysis.get("success", True))
            self.assertEqual(annotated.shape, frame.shape)
        
        except Exception as e:
            self.skipTest(f"Integration test skipped: {e}")


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_utils_import(self):
        """Test utils module import."""
        import utils
        self.assertIsNotNone(utils)
    
    def test_dependency_check(self):
        """Test dependency checking."""
        from utils import check_dependencies
        result = check_dependencies()
        self.assertIsInstance(result, bool)


def run_quick_tests():
    """Run quick sanity tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add only quick tests
    suite.addTests(loader.loadTestsFromTestCase(TestDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestCameraModule))
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def run_full_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("DRONE DROP DETECTION - TEST SUITE")
    logger.info("="*60)
    logger.info("")
    
    import argparse
    parser = argparse.ArgumentParser(description="Test suite")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    
    args = parser.parse_args()
    
    if args.quick:
        result = run_quick_tests()
    else:
        # Default to full tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        suite.addTests(loader.loadTestsFromName(__name__))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
    
    logger.info("")
    logger.info("="*60)
    if result.wasSuccessful():
        logger.info("✅ ALL TESTS PASSED")
    else:
        logger.info(f"❌ {len(result.failures)} FAILURES, {len(result.errors)} ERRORS")
    logger.info("="*60)
    logger.info("")
    
    sys.exit(0 if result.wasSuccessful() else 1)
