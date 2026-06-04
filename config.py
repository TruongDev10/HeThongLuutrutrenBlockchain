import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ULTRALYTICS_CONFIG_DIR = BASE_DIR / ".ultralytics"
ULTRALYTICS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(ULTRALYTICS_CONFIG_DIR))

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "runtime_database.db"))
UPLOAD_IMAGE_DIR = BASE_DIR / "uploads" / "images"
UPLOAD_VIDEO_DIR = BASE_DIR / "uploads" / "videos"
OUTPUT_IMAGE_DIR = BASE_DIR / "outputs" / "images"
OUTPUT_VIDEO_DIR = BASE_DIR / "outputs" / "videos"
EXPORT_DIR = BASE_DIR / "exports"
REPORT_DIR = BASE_DIR / "reports"
MODEL_DIR = BASE_DIR / "models"

MODEL_BEST = MODEL_DIR / "best.pt"
MODEL_PRETRAINED = MODEL_DIR / "yolov8n.pt"
DEFAULT_YOLO_MODEL = str(MODEL_BEST if MODEL_BEST.exists() else MODEL_PRETRAINED if MODEL_PRETRAINED.exists() else "yolov8n.pt")

SECRET_KEY = "change-this-secret-key"
MAX_CONTENT_LENGTH = 600 * 1024 * 1024
CAMERA_INDEX = 0
FRAME_WIDTH = 960
FRAME_HEIGHT = 540
DEFAULT_CONFIDENCE = 0.35
LOG_COOLDOWN_SECONDS = 1.0
BLOCKCHAIN_LOG_COOLDOWN_SECONDS = 8.0
MIN_BLOCKCHAIN_YOLO_CONFIDENCE = 0.5
COLOR_CONTOUR_FALLBACK_ENABLED = os.getenv("COLOR_CONTOUR_FALLBACK_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}

BLOCKCHAIN_ENABLED = True
BLOCKCHAIN_PROVIDER_URI = os.getenv("BLOCKCHAIN_PROVIDER_URI", "http://127.0.0.1:7545")
BLOCKCHAIN_CHAIN_ID = int(os.getenv("BLOCKCHAIN_CHAIN_ID", "1337"))
BLOCKCHAIN_CONTRACT_ADDRESS = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS", "")
BLOCKCHAIN_PRIVATE_KEY = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")
BLOCKCHAIN_ACCOUNT_ADDRESS = os.getenv("BLOCKCHAIN_ACCOUNT_ADDRESS", "")
BLOCKCHAIN_TIMEOUT_SECONDS = 8

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

COLOR_NAMES = ["red", "yellow", "blue"]

COLOR_LABELS_VI = {
    "red": "Do",
    "yellow": "Vang",
    "blue": "Xanh duong",
    "not_target_color": "Khong thuoc mau muc tieu",
    "ignored": "Bo qua",
}

COLOR_HEX = {
    "red": "#D7352E",
    "yellow": "#D8C65D",
    "blue": "#58AFD1",
    "not_target_color": "#64748b",
    "ignored": "#64748b",
}

# OpenCV HSV hue range is 0-179.
HSV_COLOR_RANGES = {
    "red": [((0, 70, 80), (12, 255, 255)), ((170, 70, 80), (179, 255, 255))],
    "yellow": [((18, 45, 90), (42, 255, 255))],
    "blue": [((85, 35, 90), (110, 255, 255))],
}

YOLO_TARGET_CLASSES = {
    "bottle",
    "cup",
    "sports ball",
    "box",
    "vase",
    "cell phone",
    "book",
    "product",
    "item",
    "object",
}

ROBOT_SERIAL_ENABLED = os.getenv("ROBOT_SERIAL_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
ROBOT_SERIAL_PORT = os.getenv("ROBOT_SERIAL_PORT", "COM3")
ROBOT_SERIAL_BAUDRATE = int(os.getenv("ROBOT_SERIAL_BAUDRATE", "9600"))
ROBOT_COMMAND_COOLDOWN_SECONDS = float(os.getenv("ROBOT_COMMAND_COOLDOWN_SECONDS", "6.0"))
ROBOT_MIN_CONFIDENCE = float(os.getenv("ROBOT_MIN_CONFIDENCE", "0.45"))
ROBOT_MIN_COLOR_RATIO = float(os.getenv("ROBOT_MIN_COLOR_RATIO", "0.12"))
