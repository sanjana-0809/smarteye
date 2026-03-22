import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURE_DIR = os.path.join(BASE_DIR, "captures")
MODEL_PATH = "yolov8n.pt"

CAMERA_INDEX = os.environ.get("VIDEO_SOURCE", "static/demo.mp4")

RESOLUTION = (320, 240)
ROTATE_FRAME = None

CONF_THRESHOLD = 0.20
IMG_SZ = 320
DETECT_EVERY_N_FRAMES = 1
SMOOTH_WINDOW = 2
HUMAN_CONFIRM_COUNT = 1
RESET_ON_NO_HUMAN_CHECKS = 10

HUMAN_NAMES = {"person"}
ANIMAL_NAMES = {"dog", "cat", "horse", "sheep", "cow", "bear", "zebra"}
VEHICLE_NAMES = {"car", "truck", "bus", "bicycle", "motorcycle"}

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

USE_MOTION_DETECTION = False
DETECTION_CACHE_SIZE = 20
MIN_DETECTION_INTERVAL = 0.1
ALERT_COOLDOWN = 5
