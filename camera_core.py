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

        logger.log("Loading AI Model...")
        try:
            self.model = YOLO(MODEL_PATH)
            self.model_ready = True
            logger.log("AI Model Loaded Successfully.")
        except Exception as e:
            logger.log(f"Error loading model: {e}")
            self.model_ready = False

        # Sliding window for false alarm reduction
        self.detect_history = deque(maxlen=10)
        self.in_alert_state = False
        self.no_object_streak = 0

        self.frame_queue = queue.Queue(maxsize=1)
        self.processing_thread = None

        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 0

        self.last_alert_time = 0
        self.alert_cooldown = ALERT_COOLDOWN
        self.consecutive_detections = 0
        self.last_detection_time = 0

    def map_label(self, name):
        n = name.lower()
        if n in HUMAN_NAMES: return "Human"
        if n in ANIMAL_NAMES: return "Animal"
        if n in VEHICLE_NAMES: return "Vehicle"
        return "Other"

    def open_camera(self):
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
            logger.log(f"Error opening video source: {e}")
            if self.cap:
                self.cap.release()
            return False

    def get_frame(self):
        with self.lock:
            return self.current_frame_encoded

    def _send_alert_async(self, frame, message):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(CAPTURE_DIR, f"alert_{timestamp}.jpg")
        os.makedirs(CAPTURE_DIR, exist_ok=True)
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        threading.Thread(
            target=send_telegram_alert,
            args=(filename, message),
            daemon=True
        ).start()
        self.last_alert_time = time.time()

    def _instant_detection(self, frame):
        if not self.model_ready:
            return frame, False

        current_time = time.time()
        if current_time - self.last_detection_time < MIN_DETECTION_INTERVAL:
            return frame, False

        detection_size = IMG_SZ
        detection_frame = cv2.resize(frame, (detection_size, detection_size))

        try:
            results = self.model(
                detection_frame,
                imgsz=detection_size,
                conf=CONF_THRESHOLD,
                verbose=False,
                max_det=5,
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

                if category == "Human":
                    human_detected = True
                    scale_x = frame.shape[1] / detection_size
                    scale_y = frame.shape[0] / detection_size
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    x1 = int(max(0, min(x1 * scale_x, frame.shape[1] - 1)))
                    y1 = int(max(0, min(y1 * scale_y, frame.shape[0] - 1)))
                    x2 = int(max(0, min(x2 * scale_x, frame.shape[1] - 1)))
                    y2 = int(max(0, min(y2 * scale_y, frame.shape[0] - 1)))

                    # Draw green box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    conf = float(box.conf[0])
                    cv2.putText(frame, f"HUMAN {conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    self.last_detection_time = current_time

        return frame, human_detected

    def _process_frames_instantly(self):
        while self.is_running:
            try:
                try:
                    frame = self.frame_queue.get_nowait()
                except queue.Empty:
                    time.sleep(0.005)
                    continue

                processed_frame, human_detected = self._instant_detection(frame.copy())

                # Sliding window — add result to history
                self.detect_history.append(1 if human_detected else 0)

                # Only trigger alert if majority of recent frames have humans
                # This reduces false alarms significantly
                window_sum = sum(self.detect_history)
                window_size = len(self.detect_history)
                detection_ratio = window_sum / window_size if window_size > 0 else 0

                if human_detected:
                    self.consecutive_detections += 1
                    self.no_object_streak = 0
                else:
                    self.consecutive_detections = 0
                    self.no_object_streak += 1

                current_time = time.time()

                # Alert only if detection ratio > 50% in sliding window
                if detection_ratio >= 0.5 and self.consecutive_detections >= HUMAN_CONFIRM_COUNT:
                    should_alert = False
                    if not self.in_alert_state:
                        should_alert = True
                        self.in_alert_state = True
                        logger.log("System ALERTED - Human Detected!")
                    elif current_time - self.last_alert_time >= self.alert_cooldown:
                        should_alert = True

                    if should_alert:
                        alert_msg = "🚨 HUMAN DETECTED!"
                        logger.log(alert_msg)
                        self._send_alert_async(processed_frame, alert_msg)

                # Reset alert state if scene is clear
                if self.in_alert_state and self.no_object_streak >= RESET_ON_NO_HUMAN_CHECKS:
                    logger.log("Scene Clear. System Re-Armed.")
                    self.in_alert_state = False
                    self.no_object_streak = 0
                    self.detect_history.clear()
                    self.consecutive_detections = 0

                # Add status overlay on frame
                status_text = "ALERTED" if self.in_alert_state else "ARMED"
                color = (0, 0, 255) if self.in_alert_state else (0, 255, 0)
                cv2.putText(processed_frame, f"STATUS: {status_text}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Update the displayed frame with processed frame (with boxes)
                with self.lock:
                    _, encoded = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    self.current_frame_encoded = encoded.tobytes()
                    self.current_frame = processed_frame

            except Exception as e:
                logger.log(f"Processing error: {e}")
                time.sleep(0.1)

    def run(self):
        logger.log("Starting Video Source...")

        while not self.open_camera():
            logger.log("Retrying video source...")
            time.sleep(2)

        self.processing_thread = threading.Thread(
            target=self._process_frames_instantly, daemon=True)
        self.processing_thread.start()

        logger.log("Feed running...")

        frame_counter = 0
        last_log_time = time.time()
        is_video_file = isinstance(CAMERA_INDEX, str)

        while self.is_running:
            try:
                ret, frame = self.cap.read()

                if not ret:
                    if is_video_file:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        logger.log("Frame read failed, reconnecting...")
                        time.sleep(0.5)
                        self.open_camera()
                        continue

                # Send frame to detection queue
                if frame_counter % DETECT_EVERY_N_FRAMES == 0:
                    try:
                        while not self.frame_queue.empty():
                            try:
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                break
                        self.frame_queue.put_nowait(frame.copy())
                    except:
                        pass

                frame_counter += 1

                # FPS tracking
                self.frame_count += 1
                current_time = time.time()
                if current_time - last_log_time >= 3.0:
                    self.fps = self.frame_count / 3.0
                    if self.fps > 0:
                        logger.log(f"Performance: {self.fps:.1f} FPS")
                    last_log_time = current_time
                    self.frame_count = 0

                time.sleep(0.01)

            except Exception as e:
                logger.log(f"Camera loop error: {e}")
                time.sleep(0.5)

        if self.cap:
            self.cap.release()
        self.is_running = False
