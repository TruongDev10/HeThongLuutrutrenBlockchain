from datetime import datetime
from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename

from config import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    EXPORT_DIR,
    OUTPUT_IMAGE_DIR,
    OUTPUT_VIDEO_DIR,
    REPORT_DIR,
    UPLOAD_IMAGE_DIR,
    UPLOAD_VIDEO_DIR,
)


def ensure_directories():
    for directory in [
        UPLOAD_IMAGE_DIR,
        UPLOAD_VIDEO_DIR,
        OUTPUT_IMAGE_DIR,
        OUTPUT_VIDEO_DIR,
        EXPORT_DIR,
        REPORT_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def timestamp_slug():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def allowed_file(filename, kind):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    if kind == "image":
        return ext in ALLOWED_IMAGE_EXTENSIONS
    if kind == "video":
        return ext in ALLOWED_VIDEO_EXTENSIONS
    return False


def unique_filename(filename):
    safe = secure_filename(filename)
    stem = Path(safe).stem or "file"
    suffix = Path(safe).suffix.lower()
    return f"{stem}_{timestamp_slug()}_{uuid4().hex[:8]}{suffix}"


def tuple_to_string(values):
    return ",".join(str(int(v)) for v in values)
