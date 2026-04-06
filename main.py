"""
Main Application: AI-Assisted Drone Drop Zone Detection System

This is the entry point for the drone monitoring application. It integrates
all modules to provide real-time detection and safe zone visualization.

Usage:
    python main.py [--use-demo] [--save-video] [--headless]

Options:
    --use-demo       Use test video instead of live RTSP feed
    --save-video     Save annotated video to disk
    --headless       Don't display video (for server mode)
"""

import sys
import time
import argparse
import os
from pathlib import Path
import logging

import cv2
import numpy as np

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from config.config import *
from src.camera import create_camera_connection
from src.detection import create_detector
from src.safe_zones import create_safe_zone_analyzer
from src.visualization import FrameAnnotator, VideoWriter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DroneDropDetection")


class DroneDropDetectionApp:
    """Main application class for drone drop zone detection."""
    
    def __init__(self, use_demo: bool = False, save_video: bool = False, headless: bool = False):
        """
        Initialize the application.
        
        Args:
            use_demo (bool): Use demo/test video instead of live feed
            save_video (bool): Save annotated video to disk
            headless (bool): Run without display
        """
        self.use_demo = use_demo
        self.save_video = save_video
        self.headless = headless
        
        self.camera = None
        self.detector = None
        self.safe_zone_analyzer = None
        self.annotator = None
        self.video_writer = None
        
        self.frame_count = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.display_fps = 0
        
        self.is_running = False
        
        logger.info("=" * 60)
        logger.info("🚁 DRONE DROP ZONE DETECTION SYSTEM INITIALIZED")
        logger.info("=" * 60)
    
    def initialize_components(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            bool: True if initialization successful
        """
        logger.info("\n📡 Step 1: Initializing Camera Connection...")
        if self.use_demo:
            # For demo, we'll create a synthetic video
            logger.info("Using synthetic demo video")
            self._create_demo_video()
            rtsp_url = "demo_video.mp4"
        else:
            rtsp_url = DRONE_RTSP_URL
        
        self.camera = create_camera_connection(rtsp_url, use_test_mode=False)
        
        if not self.camera:
            logger.error("❌ Failed to initialize camera")
            return False
        
        frame_info = self.camera.get_frame_info()
        logger.info(f"✓ Camera initialized: {frame_info['width']}x{frame_info['height']} @ {frame_info['fps']} FPS")
        
        # Initialize detector
        logger.info("\n🤖 Step 2: Loading YOLOv8 Model...")
        self.detector = create_detector(YOLO_MODEL, YOLO_CONFIDENCE_THRESHOLD)
        
        if not self.detector:
            logger.error("❌ Failed to load detector model")
            return False
        
        logger.info(f"✓ YOLOv8 model loaded: {YOLO_MODEL}")
        
        # Initialize safe zone analyzer
        logger.info("\n🎯 Step 3: Initializing Safe Zone Analyzer...")
        self.safe_zone_analyzer = create_safe_zone_analyzer(
            frame_info['width'],
            frame_info['height'],
            grid_cell_size=SAFE_ZONE_CONFIG["grid_cell_size"]
        )
        logger.info("✓ Safe zone analyzer initialized")
        
        # Initialize visualizer
        logger.info("\n🎨 Step 4: Initializing Visualization...")
        self.annotator = FrameAnnotator(frame_info['width'], frame_info['height'])
        logger.info("✓ Visualization system initialized")
        
        # Initialize video writer if needed
        if self.save_video and not self.headless:
            logger.info("\n💾 Step 5: Setting Up Video Output...")
            os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)
            
            output_file = os.path.join(
                OUTPUT_VIDEO_DIR,
                f"drone_drop_detection_{int(time.time())}.mp4"
            )
            
            self.video_writer = VideoWriter(
                output_file,
                frame_info['width'],
                frame_info['height'],
                fps=OUTPUT_VIDEO_FPS,
                codec=OUTPUT_VIDEO_CODEC,
            )
            logger.info(f"✓ Video writer initialized: {output_file}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ ALL SYSTEMS INITIALIZED SUCCESSFULLY")
        logger.info("=" * 60 + "\n")
        
        return True
    
    def run(self):
        """Main application loop."""
        if not self.initialize_components():
            logger.error("Failed to initialize components")
            return
        
        self.is_running = True
        frame_widget_count = 0
        
        logger.info("🎬 Starting real-time detection loop...\n")
        
        try:
            while self.is_running:
                # Get frame from camera
                ret, frame = self.camera.read_frame()
                
                if not ret or frame is None:
                    logger.warning("No frame available, retrying...")
                    time.sleep(0.1)
                    continue
                
                self.frame_count += 1
                frame_widget_count += 1
                
                # Run detection
                detections = self.detector.detect(frame)
                
                # Analyze safe zones
                analysis = self.safe_zone_analyzer.analyze_detections(
                    detections,
                    person_confidence_threshold=SAFE_ZONE_CONFIG["max_person_confidence"],
                    obstacle_distance_threshold=SAFE_ZONE_CONFIG["min_obstacle_distance"],
                )
                
                # Generate heatmap
                heatmap = self.safe_zone_analyzer.generate_heatmap()
                
                # Annotate frame
                annotated_frame = self.annotator.annotate_frame(
                    frame,
                    detections,
                    analysis,
                    show_confidence=SHOW_CONFIDENCE_SCORES,
                    show_fps=self.display_fps if SHOW_FPS else None,
                    heatmap_overlay=heatmap if self.frame_count % 3 == 0 else None,
                    heatmap_alpha=0.2,
                )
                
                # Get best safe zone
                best_zone = self.safe_zone_analyzer.get_best_drop_zone(analysis["safe_zones"])
                
                if best_zone and self.frame_count % 10 == 0:
                    logger.info(f"✓ Safe zone found: confidence={best_zone['confidence']:.0%}, "
                              f"area={best_zone['area']:.0f}px²")
                
                # Save frame if video writer active
                if self.video_writer:
                    self.video_writer.write_frame(annotated_frame)
                
                # Display frame
                if not self.headless:
                    cv2.imshow("Drone Drop Detection", annotated_frame)
                    
                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        logger.info("Quit command received")
                        break
                    elif key == ord('s'):
                        # Save frame
                        filename = f"drone_frame_{int(time.time())}.jpg"
                        cv2.imwrite(filename, annotated_frame)
                        logger.info(f"Frame saved: {filename}")
                    elif key == ord('p'):
                        # Pause/resume
                        logger.info("Paused. Press any key to continue...")
                        cv2.waitKey(0)
                
                # Update FPS counter every 30 frames
                if frame_widget_count >= 30:
                    current_time = time.time()
                    self.display_fps = frame_widget_count / (current_time - self.last_fps_time)
                    self.last_fps_time = current_time
                    frame_widget_count = 0
                
                    if self.frame_count % 300 == 0:  # Log every 10 seconds (300 frames)
                        threat = analysis.get("threat_summary", {})
                        logger.info(
                            f"Frame {self.frame_count} | "
                            f"FPS: {self.display_fps:.1f} | "
                            f"People: {'YES' if threat.get('people_detected') else 'NO'} | "
                            f"Open: {threat.get('open_area_ratio', 0):.0%} | "
                            f"Safe Zones: {len(analysis.get('safe_zones', []))}"
                        )
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  Interrupted by user")
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup and shutdown all components."""
        logger.info("\n🛑 Shutting down...")
        
        self.is_running = False
        
        if self.camera:
            self.camera.stop_capture()
            logger.info("✓ Camera stopped")
        
        if self.video_writer:
            self.video_writer.release()
            logger.info("✓ Video saved")
        
        cv2.destroyAllWindows()
        
        logger.info(f"\n📊 Session Statistics:")
        logger.info(f"  Total frames processed: {self.frame_count}")
        logger.info(f"  Average FPS: {self.display_fps:.1f}")
        logger.info("\n✅ Shutdown complete\n")
    
    def _create_demo_video(self):
        """Create a synthetic demo video for testing."""
        logger.info("Creating synthetic demo video...")
        
        output_path = "demo_video.mp4"
        width, height = 640, 480
        fps = 30
        duration = 10  # seconds
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame_idx in range(int(fps * duration)):
            # Create synthetic frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add gradient background
            for y in range(height):
                frame[y, :] = [50 + int(100 * y / height)] * 3
            
            # Draw some objects
            # Trees (obstacles)
            cv2.circle(frame, (150, 100), 50, (0, 100, 0), -1)
            cv2.circle(frame, (350, 200), 40, (0, 120, 0), -1)
            cv2.circle(frame, (500, 150), 45, (0, 90, 0), -1)
            
            # Person (if in first half)
            if frame_idx < fps * duration // 2:
                person_x = 100 + int(frame_idx * 2)
                cv2.rectangle(frame, (person_x, 250), (person_x + 40, 350), (0, 0, 200), -1)
                cv2.circle(frame, (person_x + 20, 240), 15, (0, 0, 200), -1)
            
            # Add timestamp
            cv2.putText(
                frame,
                f"Demo Frame {frame_idx} | {frame_idx/fps:.1f}s",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (200, 200, 200),
                2,
            )
            
            writer.write(frame)
        
        writer.release()
        logger.info(f"✓ Demo video created: {output_path}")


def print_banner():
    """Print application banner."""
    banner = r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║   🚁 DRONE DROP ZONE DETECTION SYSTEM 🚁                  ║
    ║                                                            ║
    ║   AI-Powered Safe Zone Identification                     ║
    ║   Real-Time Video Analysis with YOLOv8                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Entry point."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Drone Drop Zone Detection System"
    )
    parser.add_argument(
        "--use-demo",
        action="store_true",
        help="Use synthetic demo video instead of live RTSP feed"
    )
    parser.add_argument(
        "--save-video",
        action="store_true",
        help="Save annotated video to disk"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without display window (server mode)"
    )
    
    args = parser.parse_args()
    
    app = DroneDropDetectionApp(
        use_demo=args.use_demo,
        save_video=args.save_video,
        headless=args.headless,
    )
    
    app.run()


if __name__ == "__main__":
    main()
