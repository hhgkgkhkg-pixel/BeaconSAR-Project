"""
Visualization Module: Renders annotated video with detections and safe zones.

This module handles all visual output including bounding boxes, safe zone
overlays, confidence scores, and FPS counters.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VisualizationModule")


class FrameAnnotator:
    """
    Handles visual annotation of frames with detections and safe zones.
    
    Attributes:
        frame_width (int): Frame width
        frame_height (int): Frame height
    """
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        Initialize frame annotator.
        
        Args:
            frame_width (int): Frame width
            frame_height (int): Frame height
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        self.line_thickness = 2
    
    def annotate_frame(
        self,
        frame: np.ndarray,
        detections: Dict,
        safe_zones_analysis: Dict,
        show_confidence: bool = True,
        show_fps: float = None,
        heatmap_overlay: Optional[np.ndarray] = None,
        heatmap_alpha: float = 0.3,
    ) -> np.ndarray:
        """
        Create annotated version of frame with all visualizations.
        
        Args:
            frame (np.ndarray): Input BGR frame
            detections (Dict): Detection results from YOLO
            safe_zones_analysis (Dict): Safe zone analysis results
            show_confidence (bool): Show confidence scores on boxes
            show_fps (float): FPS to display (if not None)
            heatmap_overlay (np.ndarray): Safety heatmap to overlay
            heatmap_alpha (float): Transparency of heatmap
        
        Returns:
            np.ndarray: Annotated BGR frame
        """
        annotated = frame.copy()
        
        # Overlay heatmap if provided
        if heatmap_overlay is not None:
            annotated = cv2.addWeighted(
                annotated,
                1.0 - heatmap_alpha,
                heatmap_overlay,
                heatmap_alpha,
                0
            )
        
        # Draw detection boxes
        if detections.get("success"):
            annotated = self._draw_detection_boxes(
                annotated,
                detections,
                show_confidence
            )
        
        # Draw safe zones
        annotated = self._draw_safe_zones(annotated, safe_zones_analysis)
        
        # Draw threat summary
        annotated = self._draw_threat_summary(annotated, safe_zones_analysis)
        
        # Draw FPS counter
        if show_fps is not None:
            annotated = self._draw_fps(annotated, show_fps)
        
        # Draw inference time
        if detections.get("success"):
            annotated = self._draw_inference_time(annotated, detections)
        
        return annotated
    
    def _draw_detection_boxes(
        self,
        frame: np.ndarray,
        detections: Dict,
        show_confidence: bool = True,
    ) -> np.ndarray:
        """Draw bounding boxes for detections."""
        annotated = frame.copy()
        
        for i, box in enumerate(detections.get("boxes", [])):
            x1, y1, x2, y2 = box
            label = detections["labels"][i]
            confidence = detections["confidences"][i]
            
            # Determine color based on detection type
            if label == "person":
                color = (0, 0, 255)  # Red for people
            elif label in ["potted plant", "bicycle", "car", "motorcycle", "bus", "truck"]:
                color = (255, 165, 0)  # Orange for obstacles
            else:
                color = (0, 255, 255)  # Yellow for others
            
            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, self.line_thickness)
            
            # Draw label
            text = f"{label}"
            if show_confidence:
                text += f" {confidence:.2f}"
            
            text_size = cv2.getTextSize(text, self.font, self.font_scale, self.font_thickness)[0]
            
            # Draw text background
            cv2.rectangle(
                annotated,
                (x1, y1 - text_size[1] - 5),
                (x1 + text_size[0], y1),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                annotated,
                text,
                (x1, y1 - 5),
                self.font,
                self.font_scale,
                (255, 255, 255),
                self.font_thickness,
            )
        
        return annotated
    
    def _draw_safe_zones(self, frame: np.ndarray, analysis: Dict) -> np.ndarray:
        """Draw safe and unsafe zones."""
        annotated = frame.copy()
        
        # Draw safe zones in green
        for zone in analysis.get("safe_zones", []):
            bounds = zone["bounds"]
            x1, y1, x2, y2 = bounds
            
            # Clamp to frame
            x1 = max(0, min(x1, self.frame_width))
            y1 = max(0, min(y1, self.frame_height))
            x2 = max(0, min(x2, self.frame_width))
            y2 = max(0, min(y2, self.frame_height))
            
            # Draw rectangle with transparency
            overlay = annotated.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)  # Green fill
            annotated = cv2.addWeighted(overlay, 0.2, annotated, 0.8, 0)
            
            # Draw border
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw confidence score
            conf = zone.get("confidence", 1.0)
            text = f"SAFE {conf:.0%}"
            cv2.putText(
                annotated,
                text,
                (x1 + 5, y1 + 25),
                self.font,
                0.5,
                (0, 255, 0),
                1,
            )
        
        # Draw unsafe zones in red
        for zone in analysis.get("unsafe_zones", []):
            bounds = zone["bounds"]
            x1, y1, x2, y2 = bounds
            
            # Clamp to frame
            x1 = max(0, min(x1, self.frame_width))
            y1 = max(0, min(y1, self.frame_height))
            x2 = max(0, min(x2, self.frame_width))
            y2 = max(0, min(y2, self.frame_height))
            
            # Draw border only (red)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Draw threat level
            threat = zone.get("threat_level", 0.5)
            text = f"UNSAFE {threat:.0%}"
            cv2.putText(
                annotated,
                text,
                (x1 + 5, y1 + 25),
                self.font,
                0.5,
                (0, 0, 255),
                1,
            )
        
        return annotated
    
    def _draw_threat_summary(self, frame: np.ndarray, analysis: Dict) -> np.ndarray:
        """Draw threat summary in top-left corner."""
        annotated = frame.copy()
        threat = analysis.get("threat_summary", {})
        
        y_offset = 30
        
        # Background panel
        cv2.rectangle(annotated, (10, 10), (300, 130), (0, 0, 0), -1)
        cv2.rectangle(annotated, (10, 10), (300, 130), (200, 200, 200), 2)
        
        # Title
        cv2.putText(
            annotated,
            "THREAT ANALYSIS",
            (20, y_offset),
            self.font,
            0.7,
            (200, 200, 200),
            2,
        )
        y_offset += 30
        
        # People detected
        people_status = "PEOPLE: YES" if threat.get("people_detected") else "PEOPLE: NO"
        people_color = (0, 0, 255) if threat.get("people_detected") else (0, 255, 0)
        cv2.putText(
            annotated,
            people_status,
            (20, y_offset),
            self.font,
            0.5,
            people_color,
            1,
        )
        y_offset += 25
        
        # Open area ratio
        open_ratio = threat.get("open_area_ratio", 0.0)
        cv2.putText(
            annotated,
            f"OPEN AREA: {open_ratio:.0%}",
            (20, y_offset),
            self.font,
            0.5,
            (0, 255, 0) if open_ratio > 0.4 else (0, 165, 255),
            1,
        )
        y_offset += 25
        
        # Obstacle density
        obstacle_dens = threat.get("obstacle_density", 0.0)
        cv2.putText(
            annotated,
            f"OBSTACLES: {obstacle_dens:.0%}",
            (20, y_offset),
            self.font,
            0.5,
            (0, 255, 0) if obstacle_dens < 0.3 else (0, 0, 255),
            1,
        )
        
        return annotated
    
    def _draw_fps(self, frame: np.ndarray, fps: float) -> np.ndarray:
        """Draw FPS counter in top-right corner."""
        text = f"FPS: {fps:.1f}"
        text_size = cv2.getTextSize(text, self.font, 0.7, 2)[0]
        
        x = self.frame_width - text_size[0] - 20
        y = 30
        
        # Background
        cv2.rectangle(frame, (x - 10, y - 25), (self.frame_width - 10, y + 5), (0, 0, 0), -1)
        cv2.rectangle(frame, (x - 10, y - 25), (self.frame_width - 10, y + 5), (0, 255, 0), 2)
        
        # Text
        cv2.putText(
            frame,
            text,
            (x, y),
            self.font,
            0.7,
            (0, 255, 0),
            2,
        )
        
        return frame
    
    def _draw_inference_time(self, frame: np.ndarray, detections: Dict) -> np.ndarray:
        """Draw inference time."""
        inference_ms = detections.get("inference_time", 0) * 1000
        text = f"Inference: {inference_ms:.1f}ms"
        
        cv2.putText(
            frame,
            text,
            (10, self.frame_height - 20),
            self.font,
            0.5,
            (200, 200, 200),
            1,
        )
        
        return frame
    
    def draw_status_message(
        self,
        frame: np.ndarray,
        message: str,
        status_type: str = "info",
        duration: int = 3,
    ) -> np.ndarray:
        """
        Draw a status message on frame.
        
        Args:
            frame (np.ndarray): Input frame
            message (str): Message text
            status_type (str): 'info', 'success', 'error', 'warning'
            duration (int): Display duration in frames
        
        Returns:
            np.ndarray: Frame with message
        """
        color_map = {
            "info": (200, 200, 200),      # Gray
            "success": (0, 255, 0),       # Green
            "error": (0, 0, 255),         # Red
            "warning": (0, 165, 255),     # Orange
        }
        
        color = color_map.get(status_type, color_map["info"])
        
        # Background panel
        panel_height = 50
        cv2.rectangle(frame, (0, 0), (self.frame_width, panel_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, 0), (self.frame_width, panel_height), color, 3)
        
        # Text
        cv2.putText(
            frame,
            message,
            (20, 35),
            self.font,
            0.7,
            color,
            2,
        )
        
        return frame


class VideoWriter:
    """Handles saving annotated video to disk."""
    
    def __init__(
        self,
        output_path: str,
        frame_width: int,
        frame_height: int,
        fps: float = 20.0,
        codec: str = "mp4v",
    ):
        """
        Initialize video writer.
        
        Args:
            output_path (str): Path to output video file
            frame_width (int): Frame width
            frame_height (int): Frame height
            fps (float): Frames per second
            codec (str): Video codec
        """
        self.output_path = output_path
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        
        # Get codec code
        fourcc = cv2.VideoWriter_fourcc(*codec)
        
        self.writer = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            (frame_width, frame_height),
        )
        
        if not self.writer.isOpened():
            logger.error(f"Failed to open video writer: {output_path}")
        else:
            logger.info(f"✓ Video writer initialized: {output_path}")
    
    def write_frame(self, frame: np.ndarray):
        """Write a frame to video."""
        if self.writer and self.writer.isOpened():
            # Ensure frame has correct size
            if frame.shape[:2] != (self.frame_height, self.frame_width):
                frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            
            self.writer.write(frame)
    
    def release(self):
        """Release video writer."""
        if self.writer:
            self.writer.release()
            logger.info(f"✓ Video saved: {self.output_path}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
