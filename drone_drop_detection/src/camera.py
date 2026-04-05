"""
Camera Module: Handles video capture from RTSP drone feed or test video.

This module manages the connection to the drone's RTSP feed and provides
video frame streaming functionality. It includes error handling and retry logic.
"""

import cv2
import threading
import time
from queue import Queue
from typing import Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CameraModule")


class CameraCapture:
    """
    Handles video capture from RTSP drone feed or test video source.
    
    Attributes:
        rtsp_url (str): RTSP stream URL
        frame_queue (Queue): Queue for storing captured frames
        is_running (bool): Flag to indicate if capture is active
        frame_width (int): Width of captured frames
        frame_height (int): Height of captured frames
        fps (float): Frames per second of the video source
    """
    
    def __init__(self, rtsp_url: str, max_queue_size: int = 10, use_threading: bool = True):
        """
        Initialize camera capture.
        
        Args:
            rtsp_url (str): RTSP URL of the drone feed
            max_queue_size (int): Maximum frames to buffer
            use_threading (bool): Use threading for capture
        """
        self.rtsp_url = rtsp_url
        self.frame_queue = Queue(maxsize=max_queue_size)
        self.is_running = False
        self.capture = None
        self.frame_width = 0
        self.frame_height = 0
        self.fps = 0
        self.use_threading = use_threading
        self.capture_thread = None
        self.frame_count = 0
        self.last_frame = None
    
    def connect(self) -> bool:
        """
        Connect to the RTSP stream with retry logic.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to {self.rtsp_url} (attempt {attempt + 1}/{max_retries})")
                
                self.capture = cv2.VideoCapture(self.rtsp_url)
                
                # Set connection timeout properties
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                
                # Verify connection by trying to read a frame
                ret, frame = self.capture.read()
                
                if ret and frame is not None:
                    self.frame_height, self.frame_width = frame.shape[:2]
                    self.fps = self.capture.get(cv2.CAP_PROP_FPS)
                    if self.fps == 0:
                        self.fps = 30  # Default FPS
                    
                    logger.info(f"✓ Connected to drone feed: {self.frame_width}x{self.frame_height} @ {self.fps} FPS")
                    self.last_frame = frame
                    return True
                else:
                    logger.warning("Failed to read frame from stream")
                    self.capture.release()
                    self.capture = None
                    
            except Exception as e:
                logger.warning(f"Connection attempt failed: {e}")
                if self.capture:
                    self.capture.release()
                    self.capture = None
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        logger.error("Failed to connect to drone RTSP feed")
        return False
    
    def start_capture(self):
        """Start capturing frames (threaded or blocking)."""
        if not self.capture:
            logger.error("Camera not connected. Call connect() first.")
            return
        
        self.is_running = True
        
        if self.use_threading:
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            logger.info("Frame capture started (threaded mode)")
        else:
            logger.info("Frame capture started (on-demand mode)")
    
    def _capture_loop(self):
        """Internal loop for continuous frame capture (runs in thread)."""
        while self.is_running:
            try:
                ret, frame = self.capture.read()
                
                if not ret or frame is None:
                    logger.warning("Failed to read frame, attempting reconnect...")
                    if self.connect():
                        continue
                    else:
                        break
                
                self.last_frame = frame
                self.frame_count += 1
                
                # Non-blocking put (discard oldest if queue is full)
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    try:
                        self.frame_queue.get_nowait()  # Remove oldest
                        self.frame_queue.put_nowait(frame)  # Add newest
                    except:
                        pass
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
    
    def read_frame(self) -> Optional[Tuple[bool, Optional[Any]]]:
        """
        Read a frame from the queue or directly from capture.
        
        Returns:
            Tuple[bool, frame]: (success, frame) where success=True if frame available
        """
        if self.use_threading:
            try:
                frame = self.frame_queue.get(timeout=1)
                return True, frame
            except:
                return False, self.last_frame
        else:
            # Direct read mode
            if self.capture:
                ret, frame = self.capture.read()
                if ret:
                    self.last_frame = frame
                    self.frame_count += 1
                return ret, frame
            return False, self.last_frame
    
    def get_frame_info(self) -> dict:
        """Get information about the current video stream."""
        return {
            "width": self.frame_width,
            "height": self.frame_height,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "url": self.rtsp_url,
        }
    
    def stop_capture(self):
        """Stop capturing frames and release resources."""
        self.is_running = False
        
        if self.use_threading and self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        logger.info("Frame capture stopped")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_capture()


def create_camera_connection(rtsp_url: str, use_test_mode: bool = False) -> Optional[CameraCapture]:
    """
    Factory function to create and initialize camera connection.
    
    Args:
        rtsp_url (str): RTSP URL for drone feed
        use_test_mode (bool): Use test video instead of RTSP
    
    Returns:
        CameraCapture: Initialized camera object or None if connection fails
    """
    camera = CameraCapture(rtsp_url, use_threading=True)
    
    if camera.connect():
        camera.start_capture()
        return camera
    else:
        logger.error("Could not establish camera connection")
        return None
