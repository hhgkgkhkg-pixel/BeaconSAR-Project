"""
AI Detection Module: Handles YOLOv8 object detection on video frames.

This module runs the pre-trained YOLOv8 model on frames to detect objects
(people, vehicles, obstacles, etc.) needed for safe zone identification.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
from typing import List, Dict, Tuple, Optional
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIDetectionModule")


class YOLODetector:
    """
    YOLOv8-based object detector for drone monitoring.
    
    Attributes:
        model (YOLO): YOLOv8 model instance
        confidence_threshold (float): Minimum confidence for detections
        iou_threshold (float): IOU threshold for NMS
        device (str): 'cuda' if GPU available, else 'cpu'
    """
    
    def __init__(self, model_name: str = "yolov8n.pt", conf_threshold: float = 0.5):
        """
        Initialize YOLOv8 detector.
        
        Args:
            model_name (str): YOLOv8 model size (n/s/m/l/x)
            conf_threshold (float): Confidence threshold for detections
        """
        self.model_name = model_name
        self.confidence_threshold = conf_threshold
        self.model = None
        self.device = None
        self.frame_width = 0
        self.frame_height = 0
        self.inference_time = 0
        self.detections_cache = []
    
    def load_model(self) -> bool:
        """
        Load YOLOv8 model.
        
        Returns:
            bool: True if model loaded successfully
        """
        try:
            # Determine device (GPU or CPU)
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("✓ GPU detected, using CUDA")
            else:
                self.device = "cpu"
                logger.info("Using CPU for inference")
            
            # Load model
            logger.info(f"Loading YOLOv8 model: {self.model_name}")
            self.model = YOLO(self.model_name)
            self.model.to(self.device)
            
            logger.info(f"✓ Model loaded successfully on {self.device}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def detect(self, frame: np.ndarray) -> Dict:
        """
        Run YOLO inference on a frame.
        
        Args:
            frame (np.ndarray): Input BGR frame from OpenCV
        
        Returns:
            Dict: Detection results with boxes, confidences, classes, and labels
        """
        if self.model is None:
            logger.error("Model not loaded")
            return {"success": False}
        
        try:
            # Store frame dimensions
            self.frame_height, self.frame_width = frame.shape[:2]
            
            # Run inference
            import time
            start_time = time.time()
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            self.inference_time = time.time() - start_time
            
            # Extract detections
            detections = {
                "success": True,
                "boxes": [],      # [x1, y1, x2, y2] normalized
                "confidences": [],
                "class_ids": [],
                "labels": [],
                "raw_results": results,
                "inference_time": self.inference_time,
            }
            
            for result in results:
                if result.boxes is None or len(result.boxes) == 0:
                    continue
                
                boxes = result.boxes.cpu().numpy()
                
                for box in boxes:
                    # Get coordinates (normalized)
                    x1, y1, x2, y2 = box.xyxyn[0]
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    label = result.names[class_id]
                    
                    # Convert to pixel coordinates
                    x1_px = int(x1 * self.frame_width)
                    y1_px = int(y1 * self.frame_height)
                    x2_px = int(x2 * self.frame_width)
                    y2_px = int(y2 * self.frame_height)
                    
                    detections["boxes"].append((x1_px, y1_px, x2_px, y2_px))
                    detections["confidences"].append(confidence)
                    detections["class_ids"].append(class_id)
                    detections["labels"].append(label)
            
            self.detections_cache = detections
            return detections
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return {"success": False, "error": str(e)}
    
    def filter_detections_by_class(self, detections: Dict, target_classes: List[str]) -> Dict:
        """
        Filter detections to only include specific classes.
        
        Args:
            detections (Dict): Raw detections from detect()
            target_classes (List[str]): Class names to keep
        
        Returns:
            Dict: Filtered detections
        """
        if not detections.get("success"):
            return detections
        
        filtered = {
            "success": True,
            "boxes": [],
            "confidences": [],
            "class_ids": [],
            "labels": [],
        }
        
        for i, label in enumerate(detections["labels"]):
            if label in target_classes:
                filtered["boxes"].append(detections["boxes"][i])
                filtered["confidences"].append(detections["confidences"][i])
                filtered["class_ids"].append(detections["class_ids"][i])
                filtered["labels"].append(label)
        
        return filtered
    
    def get_detections_by_class(self, detections: Dict, class_name: str) -> List[Dict]:
        """
        Get all detections for a specific class.
        
        Args:
            detections (Dict): Detection results
            class_name (str): Target class name
        
        Returns:
            List[Dict]: List of detections for that class
        """
        results = []
        for i, label in enumerate(detections.get("labels", [])):
            if label == class_name:
                results.append({
                    "box": detections["boxes"][i],
                    "confidence": detections["confidences"][i],
                    "class_id": detections["class_ids"][i],
                    "label": label,
                })
        return results
    
    def count_detections_by_class(self, detections: Dict) -> Dict[str, int]:
        """Count detections grouped by class."""
        counts = {}
        for label in detections.get("labels", []):
            counts[label] = counts.get(label, 0) + 1
        return counts
    
    def get_confidence_for_class(self, detections: Dict, class_name: str) -> List[float]:
        """Get all confidence scores for a specific class."""
        confidences = []
        for i, label in enumerate(detections.get("labels", [])):
            if label == class_name:
                confidences.append(detections["confidences"][i])
        return confidences
    
    def get_inference_stats(self) -> Dict:
        """Get inference performance statistics."""
        return {
            "inference_time_ms": self.inference_time * 1000,
            "fps": 1 / self.inference_time if self.inference_time > 0 else 0,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "device": self.device,
        }


def create_detector(model_name: str = "yolov8n.pt", conf_threshold: float = 0.5) -> Optional[YOLODetector]:
    """
    Factory function to create and load a YOLOv8 detector.
    
    Args:
        model_name (str): YOLOv8 model size
        conf_threshold (float): Confidence threshold
    
    Returns:
        YOLODetector: Initialized detector or None if loading failed
    """
    detector = YOLODetector(model_name, conf_threshold)
    if detector.load_model():
        return detector
    return None
