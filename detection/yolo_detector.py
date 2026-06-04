import cv2
import numpy as np

from config import (
    COLOR_CONTOUR_FALLBACK_ENABLED,
    DEFAULT_CONFIDENCE,
    DEFAULT_YOLO_MODEL,
    HSV_COLOR_RANGES,
    YOLO_TARGET_CLASSES,
)


class YOLODetector:
    def __init__(self, model_path=DEFAULT_YOLO_MODEL):
        self.model_path = model_path
        self.model = None
        self.model_error = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO

            self.model = YOLO(self.model_path)
        except Exception as exc:
            self.model_error = str(exc)
            self.model = None

    def detect(self, frame, confidence=DEFAULT_CONFIDENCE):
        if self.model is None:
            return self._detect_by_contours(frame, confidence)

        detections = []
        results = self.model.predict(frame, conf=float(confidence), verbose=False, imgsz=640)
        names = getattr(self.model, "names", {})
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                object_name = names.get(cls_id, "object") if isinstance(names, dict) else "object"
                if object_name == "person":
                    continue
                if YOLO_TARGET_CLASSES and object_name not in YOLO_TARGET_CLASSES:
                    continue
                clipped_box = self._clip_box((x1, y1, x2, y2), frame)
                if self._is_unusable_box(clipped_box, frame):
                    continue
                detections.append(
                    {
                        "box": clipped_box,
                        "confidence": conf,
                        "class_id": cls_id,
                        "object_name": object_name,
                        "source": "yolov8",
                    }
                )
        if not detections and COLOR_CONTOUR_FALLBACK_ENABLED:
            return self._detect_by_contours(frame, confidence, source="contour-empty-yolo")
        return detections

    def _detect_by_contours(self, frame, confidence, source="color-contour"):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        color_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for ranges in HSV_COLOR_RANGES.values():
            for lower, upper in ranges:
                color_mask = cv2.bitwise_or(color_mask, cv2.inRange(hsv, np.array(lower), np.array(upper)))
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = frame.shape[:2]
        min_area = max(1600, int(w * h * 0.01))
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            x, y, bw, bh = cv2.boundingRect(contour)
            if bw < 30 or bh < 30:
                continue
            box = self._clip_box((x, y, x + bw, y + bh), frame)
            if self._is_unusable_box(box, frame):
                continue
            detections.append(
                    {
                        "box": box,
                        "confidence": max(float(confidence), 0.45),
                        "class_id": -1,
                        "object_name": "color_region",
                        "source": source,
                    }
                )
        detections.sort(key=lambda item: (item["box"][2] - item["box"][0]) * (item["box"][3] - item["box"][1]), reverse=True)
        return detections[:12]

    def _clip_box(self, box, frame):
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = box
        return max(0, x1), max(0, y1), min(w - 1, x2), min(h - 1, y2)

    def _is_unusable_box(self, box, frame):
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = box
        area_ratio = ((x2 - x1) * (y2 - y1)) / max(w * h, 1)
        return area_ratio < 0.004 or area_ratio > 0.72
