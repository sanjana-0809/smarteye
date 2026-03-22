import cv2
import time
import threading
import os
import queue
from collections import deque
from datetime import datetime
from ultralytics import YOLO
from config import *
from notifier import send_telegram_alert
from log_manager import logger

class CameraCore:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_frame = None
        self.current_frame_encoded = None
        self.is_running = True
        self.cap = None
        
        # Load model immediately
        logger.log("Loading AI Model...")
        try:
            self.model = YOLO(MODEL_PATH)
            self.model_ready = True
            logger.log("AI Model Loaded Successfully.")
        except Exception as e:
            logger.log(f"Error loading model: {e}")
            self.model_ready = False
        
        self.detect_history = deque(maxlen=SMOOTH_WINDOW)
        self.in_alert_state = False
        self.no_object_streak = 0
        
        # Frame queue for async processing
        self.frame_queue = queue.Queue(maxsize=1)
        self.processing_thread = None
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 0
        
        # Alert management
        self.last_alert_time = 0
        self.alert_cooldown = ALERT_COOLDOWN
        self.consecutive_detections = 0
        
        # Ultra-fast detection flag
        self.last_detection_time = 0

    def map_label(self, name):
        """Use YOUR label mapping from config"""
        n = name.lower()
        if n in HUMAN_NAMES: return "Human"
        if n in ANIMAL_NAMES: return "Animal"
        if n in VEHICLE_NAMES: return "Vehicle"
        return "Other"

    def open_camera(self):
        """Camera connection - optimized for ultra-fast detection"""
        if self.cap is not None:
            self.cap.release()
            time.sleep(0.1)
        
        try:
            self.cap = cv2.VideoCapture(CAMERA_INDEX)
            if not self.cap.isOpened():
                logger.log(f"Cannot open video source: {CAMERA_INDEX}")
                return False
            logger.log(f"Video source opened: {CAMERA_INDEX}")
            return True
                
        except Exception as e:
            logger.log(f"Camera Error: {e}")
            if self.cap:
                self.cap.release()
            return False

    def get_frame(self):
        """Return pre-encoded frame for instant access"""
        with self.lock:
            return self.current_frame_encoded

    def _send_alert_async(self, frame, message):
        """Send alert without blocking"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(CAPTURE_DIR, f"alert_{timestamp}.jpg")
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        
        # Quick save
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        
        # Send in background
        threading.Thread(
            target=send_telegram_alert,
            args=(filename, message),
            daemon=True
        ).start()
        
        self.last_alert_time = time.time()
        return True

    def _instant_detection(self, frame):
        """Ultra-fast human detection"""
        if not self.model_ready:
            return frame, False
        
        current_time = time.time()
        
        # Skip if detection was too recent
        if current_time - self.last_detection_time < MIN_DETECTION_INTERVAL:
            return frame, False
        
        # Use tiny frame for ultra-fast detection
        detection_size = IMG_SZ
        detection_frame = cv2.resize(frame, (detection_size, detection_size))
        
        try:
            # Ultra-fast inference
            results = self.model(
                detection_frame, 
                imgsz=detection_size,
                conf=CONF_THRESHOLD,
                verbose=False,
                max_det=1,  # Only look for 1 object (humans)
                device='cpu'
            )[0]
        except Exception as e:
            logger.log(f"Inference error: {e}")
            return frame, False
        
        human_detected = False
        
        if results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                name = results.names[cls_id]
                category = self.map_label(name)
                conf = float(box.conf[0])
                
                if category == "Human":
                    human_detected = True
                    
                    # Scale coordinates
                    scale_x = frame.shape[1] / detection_size
                    scale_y = frame.shape[0] / detection_size
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)
                    
                    # Ensure within bounds
                    x1 = max(0, min(x1, frame.shape[1] - 1))
                    y1 = max(0, min(y1, frame.shape[0] - 1))
                    x2 = max(0, min(x2, frame.shape[1] - 1))
                    y2 = max(0, min(y2, frame.shape[0] - 1))
                    
                    # Draw box
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"HUMAN", (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    self.last_detection_time = current_time
                    break
        
        return frame, human_detected

    def _process_frames_instantly(self):
        """Continuous frame processing for instant detection"""
        while self.is_running:
            try:
                # Get latest frame
                try:
                    frame = self.frame_queue.get_nowait()
                except queue.Empty:
                    time.sleep(0.005)  # Very short sleep
                    continue
                
                # Process detection
                start_time = time.time()
                processed_frame, human_detected = self._instant_detection(frame.copy())
                detection_time = (time.time() - start_time) * 1000
                
                # Update history
                self.detect_history.append(human_detected)
                
                # Track detections
                if human_detected:
                    self.consecutive_detections += 1
                    self.no_object_streak = 0
                else:
                    self.consecutive_detections = 0
                    self.no_object_streak += 1
                
                # **INSTANT ALERT LOGIC**
                current_time = time.time()
                
                if human_detected and self.consecutive_detections >= HUMAN_CONFIRM_COUNT:
                    # Check if we should alert
                    should_alert = False
                    
                    if not self.in_alert_state:
                        # First detection - alert immediately
                        should_alert = True
                        self.in_alert_state = True
                        logger.log("System ALERTED - Human Detected!")
                    elif current_time - self.last_alert_time >= self.alert_cooldown:
                        # Subsequent detection after cooldown
                        should_alert = True
                    
                    # Send alert
                    if should_alert:
                        alert_msg = "🚨 HUMAN DETECTED!"
                        logger.log(alert_msg)
                        self._send_alert_async(processed_frame, alert_msg)
                
                # Reset if no humans for a while
                if self.in_alert_state and self.no_object_streak >= RESET_ON_NO_HUMAN_CHECKS:
                    logger.log("Scene Clear. System Re-Armed.")
                    self.in_alert_state = False
                    self.no_object_streak = 0
                    self.detect_history.clear()
                    self.consecutive_detections = 0
                
                # Add status overlay
                status_text = "ALERTED" if self.in_alert_state else "ARMED"
                color = (0, 0, 255) if self.in_alert_state else (0, 255, 0)
                cv2.putText(processed_frame, f"STATUS: {status_text}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Add detection info
                detect_text = f"DETECT: {'HUMAN' if human_detected else 'CLEAR'}"
                detect_color = (0, 255, 0) if human_detected else (255, 255, 255)
                cv2.putText(processed_frame, detect_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, detect_color, 1)
                
                # Add performance info (if fast)
                if detection_time < 100:  # Only show if < 100ms
                    cv2.putText(processed_frame, f"Speed: {detection_time:.0f}ms", 
                               (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Update displayed frame
                with self.lock:
                    _, encoded = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    self.current_frame_encoded = encoded.tobytes()
                    self.current_frame = processed_frame
                    
            except Exception as e:
                logger.log(f"Processing error: {e}")
                time.sleep(0.1)

    def run(self):
        """Main camera loop - optimized for instant response"""
        logger.log("Starting Camera Loop...")
        
        while not self.open_camera():
            logger.log("Retrying camera connection...")
            time.sleep(1)
        
        # Start continuous processing
        self.processing_thread = threading.Thread(target=self._process_frames_instantly, daemon=True)
        self.processing_thread.start()
        
        logger.log("Camera loop running...")
        
        frame_counter = 0
        last_log_time = time.time()
        
        while self.is_running:
            try:
                # Read frame
                ret, frame = self.cap.read()
                
                if not ret:
                    if isinstance(CAMERA_INDEX, str):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    logger.log("Frame read failed, reconnecting...")
                    time.sleep(0.5)
                    self.open_camera()
                    continue
                
                # Update web frame immediately
                with self.lock:
                    self.current_frame = frame
                    # Fast encoding for web
                    _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    self.current_frame_encoded = encoded.tobytes()
                
                # **ALWAYS send to detection (every frame)**
                if frame_counter % DETECT_EVERY_N_FRAMES == 0:
                    try:
                        # Clear old frames, keep only latest
                        while not self.frame_queue.empty():
                            try:
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                break
                        self.frame_queue.put_nowait(frame.copy())
                    except:
                        pass  # Ignore queue issues
                
                frame_counter += 1
                
                # Performance logging
                self.frame_count += 1
                current_time = time.time()
                if current_time - last_log_time >= 3.0:
                    self.fps = self.frame_count / 3.0
                    if self.fps > 0:
                        logger.log(f"Performance: {self.fps:.1f} FPS")
                    last_log_time = current_time
                    self.frame_count = 0
                
                # Minimal sleep for responsiveness
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                logger.log(f"Camera loop error: {e}")
                time.sleep(0.5)
        
        # Cleanup
        if self.cap:
            self.cap.release()
        self.is_running = False
