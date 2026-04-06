"""
Safe Zone Identification Module: Analyzes detections to identify safe drop zones.

This module implements the logic for determining which areas of the video feed
are safe for drone sensor drops based on detected objects and obstacle density.
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SafeZoneModule")


class SafeZoneAnalyzer:
    """
    Analyzes frame regions to identify safe drop zones.
    
    Attributes:
        frame_width (int): Width of analyzed frames
        frame_height (int): Height of analyzed frames
        grid_cell_size (int): Size of grid cells for region analysis
    """
    
    def __init__(self, frame_width: int, frame_height: int, grid_cell_size: int = 50):
        """
        Initialize safe zone analyzer.
        
        Args:
            frame_width (int): Frame width in pixels
            frame_height (int): Frame height in pixels
            grid_cell_size (int): Size of grid cells for analysis
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.grid_cell_size = grid_cell_size
        self.grid_width = (frame_width + grid_cell_size - 1) // grid_cell_size
        self.grid_height = (frame_height + grid_cell_size - 1) // grid_cell_size
        self.safety_grid = np.ones((self.grid_height, self.grid_width), dtype=np.float32)
    
    def analyze_detections(
        self,
        detections: Dict,
        person_confidence_threshold: float = 0.3,
        obstacle_distance_threshold: float = 2.0,
    ) -> Dict:
        """
        Analyze detections to create a safety map.
        
        Args:
            detections (Dict): YOLO detection results
            person_confidence_threshold (float): Max confidence for safe person detection
            obstacle_distance_threshold (float): Min clearance from obstacles
        
        Returns:
            Dict: Safety analysis with zones and scores
        """
        # Reset safety grid
        self.safety_grid = np.ones((self.grid_height, self.grid_width), dtype=np.float32)
        
        analysis = {
            "success": True,
            "safety_grid": self.safety_grid.copy(),
            "safe_zones": [],
            "unsafe_zones": [],
            "zones_by_threat": {
                "people": [],
                "obstacles": [],
                "mixed": [],
            },
            "threat_summary": {
                "people_detected": False,
                "obstacle_density": 0.0,
                "open_area_ratio": 0.0,
            },
        }
        
        if not detections.get("success") or len(detections.get("labels", [])) == 0:
            # No detections = entire frame is potentially safe
            analysis["safe_zones"] = self._get_grid_regions_safe()
            return analysis
        
        # Process each detection
        for i, label in enumerate(detections["labels"]):
            box = detections["boxes"][i]
            confidence = detections["confidences"][i]
            
            if label == "person":
                if confidence > person_confidence_threshold:
                    self._mark_unsafe_zone(box, threat_type="person", confidence=confidence)
                analysis["threat_summary"]["people_detected"] = True
            
            elif label in ["potted plant", "bicycle", "car", "motorcycle", "bus", "truck"]:
                self._mark_unsafe_zone(box, threat_type="obstacle", confidence=confidence)
        
        # Identify safe and unsafe zones from grid
        analysis["safe_zones"] = self._get_safe_zones()
        analysis["unsafe_zones"] = self._get_unsafe_zones()
        
        # Calculate statistics
        total_cells = self.grid_width * self.grid_height
        safe_cells = np.sum(self.safety_grid > 0.5)
        analysis["threat_summary"]["open_area_ratio"] = safe_cells / total_cells
        analysis["threat_summary"]["obstacle_density"] = 1.0 - (safe_cells / total_cells)
        
        analysis["safety_grid"] = self.safety_grid.copy()
        
        return analysis
    
    def _mark_unsafe_zone(self, box: Tuple, threat_type: str = "unknown", confidence: float = 1.0):
        """
        Mark a region around detection as unsafe.
        
        Args:
            box (Tuple): (x1, y1, x2, y2) in pixels
            threat_type (str): Type of threat (person, obstacle, etc.)
            confidence (float): Detection confidence
        """
        x1, y1, x2, y2 = box
        
        # Add buffer around detection
        buffer = self.grid_cell_size
        x1 = max(0, x1 - buffer)
        y1 = max(0, y1 - buffer)
        x2 = min(self.frame_width, x2 + buffer)
        y2 = min(self.frame_height, y2 + buffer)
        
        # Convert to grid coordinates
        grid_x1 = x1 // self.grid_cell_size
        grid_y1 = y1 // self.grid_cell_size
        grid_x2 = (x2 + self.grid_cell_size - 1) // self.grid_cell_size
        grid_y2 = (y2 + self.grid_cell_size - 1) // self.grid_cell_size
        
        # Clamp to grid bounds
        grid_x1 = max(0, min(grid_x1, self.grid_width - 1))
        grid_y1 = max(0, min(grid_y1, self.grid_height - 1))
        grid_x2 = min(self.grid_width, grid_x2)
        grid_y2 = min(self.grid_height, grid_y2)
        
        # Mark cells as unsafe (reduce safety score based on confidence)
        self.safety_grid[grid_y1:grid_y2, grid_x1:grid_x2] *= (1.0 - confidence * 0.8)
    
    def _get_safe_zones(self) -> List[Dict]:
        """
        Extract contiguous safe zones from safety grid.
        
        Returns:
            List[Dict]: List of safe zones with coordinates and confidence
        """
        safe_zones = []
        
        # Find regions where safety > 0.5 (more safe than unsafe)
        safe_mask = (self.safety_grid > 0.5).astype(np.uint8)
        
        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(safe_mask)
        
        for i in range(1, num_labels):  # Skip background (0)
            x, y, w, h, area = stats[i]
            
            # Only consider reasonably sized zones
            min_area = (self.grid_cell_size // 2) ** 2
            if area < min_area:
                continue
            
            avg_safety = np.mean(self.safety_grid[labels == i])
            
            safe_zones.append({
                "center": (
                    x * self.grid_cell_size + w * self.grid_cell_size // 2,
                    y * self.grid_cell_size + h * self.grid_cell_size // 2,
                ),
                "bounds": (
                    x * self.grid_cell_size,
                    y * self.grid_cell_size,
                    (x + w) * self.grid_cell_size,
                    (y + h) * self.grid_cell_size,
                ),
                "confidence": avg_safety,
                "area": area * self.grid_cell_size ** 2,
            })
        
        # Sort by confidence (highest first)
        safe_zones.sort(key=lambda z: z["confidence"], reverse=True)
        return safe_zones
    
    def _get_unsafe_zones(self) -> List[Dict]:
        """
        Extract contiguous unsafe zones from safety grid.
        
        Returns:
            List[Dict]: List of unsafe zones
        """
        unsafe_zones = []
        
        # Find regions where safety <= 0.5 (unsafe)
        unsafe_mask = (self.safety_grid <= 0.5).astype(np.uint8)
        
        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(unsafe_mask)
        
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]
            
            min_area = (self.grid_cell_size // 4) ** 2
            if area < min_area:
                continue
            
            threat_level = 1.0 - np.mean(self.safety_grid[labels == i])
            
            unsafe_zones.append({
                "center": (
                    x * self.grid_cell_size + w * self.grid_cell_size // 2,
                    y * self.grid_cell_size + h * self.grid_cell_size // 2,
                ),
                "bounds": (
                    x * self.grid_cell_size,
                    y * self.grid_cell_size,
                    (x + w) * self.grid_cell_size,
                    (y + h) * self.grid_cell_size,
                ),
                "threat_level": threat_level,
                "area": area * self.grid_cell_size ** 2,
            })
        
        return unsafe_zones
    
    def _get_grid_regions_safe(self) -> List[Dict]:
        """Get regions when grid is fully safe (no detections)."""
        # Return one zone covering entire frame
        return [{
            "center": (self.frame_width // 2, self.frame_height // 2),
            "bounds": (0, 0, self.frame_width, self.frame_height),
            "confidence": 1.0,
            "area": self.frame_width * self.frame_height,
        }]
    
    def get_best_drop_zone(self, safe_zones: List[Dict]) -> Optional[Dict]:
        """
        Get the best safe zone for dropping sensor.
        
        Returns:
            Dict: Best safe zone or None if no safe zones
        """
        if not safe_zones:
            return None
        
        # Sort by confidence * area (prefer large, safe zones)
        safe_zones.sort(key=lambda z: z["confidence"] * z["area"], reverse=True)
        return safe_zones[0]
    
    def generate_heatmap(self) -> np.ndarray:
        """
        Generate visual heatmap of safety grid.
        
        Returns:
            np.ndarray: RGB heatmap image
        """
        # Scale grid to frame dimensions
        heatmap = cv2.resize(
            self.safety_grid,
            (self.frame_width, self.frame_height),
            interpolation=cv2.INTER_LINEAR
        )
        
        # Convert to BGR color heatmap
        heatmap_normalized = (heatmap * 255).astype(np.uint8)
        
        # Create RGB heatmap (green for safe, red for unsafe)
        heatmap_bgr = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        
        # Red for unsafe (B=0, G=0, R=255)
        heatmap_bgr[:, :, 2] = 255 - heatmap_normalized
        
        # Green for safe (B=0, G=255, R=0)
        heatmap_bgr[:, :, 1] = heatmap_normalized
        
        return heatmap_bgr
    
    def update_frame_dimensions(self, frame_width: int, frame_height: int):
        """Update analyzer for new frame size."""
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.grid_width = (frame_width + self.grid_cell_size - 1) // self.grid_cell_size
        self.grid_height = (frame_height + self.grid_cell_size - 1) // self.grid_cell_size
        self.safety_grid = np.ones((self.grid_height, self.grid_width), dtype=np.float32)


def create_safe_zone_analyzer(frame_width: int, frame_height: int, grid_cell_size: int = 50) -> SafeZoneAnalyzer:
    """Factory function to create safe zone analyzer."""
    return SafeZoneAnalyzer(frame_width, frame_height, grid_cell_size)
