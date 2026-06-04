import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from config import COLOR_HEX, COLOR_LABELS_VI, COLOR_NAMES, OUTPUT_IMAGE_DIR
from detection.color_detector import ColorDetector
from detection.robot_controller import RobotArmController
from detection.robot_simulator import RobotArmSimulator
from detection.yolo_detector import YOLODetector
from utils.helpers import timestamp_slug, tuple_to_string


class VideoProcessor:
    def __init__(self):
        self.detector = YOLODetector()
        self.color_detector = ColorDetector()
        self.robot_simulator = RobotArmSimulator()
        self.robot_controller = RobotArmController()
        self.last_log_time = 0.0
        self.target_color = None
        self.confidence = 0.35
        self.blockchain_last_log = {}
        self.latest_payload = self._empty_payload()

    def set_target_color(self, color):
        self.target_color = color if color and color != "none" else None

    def set_confidence(self, confidence):
        self.confidence = min(max(float(confidence), 0.05), 0.95)

    def process_frame(self, frame, persist_logs=True, save_defects=True, control_robot=False):
        started = time.perf_counter()
        annotated = frame.copy()
        events = []
        color_counter = Counter()

        roi_detection = self._detect_roi_color_object(frame, annotated)
        if roi_detection:
            detected_color = roi_detection["detected_color"]
            color_counter[detected_color] += 1
            status = self._resolve_status(detected_color)
            robot_plan = self.robot_simulator.create_plan(detected_color, roi_detection["box"], frame.shape, status)

            product_id = f"PRD-{timestamp_slug()}-{uuid4().hex[:6].upper()}"
            result_hash = self._make_result_hash(
                product_id,
                roi_detection["object_name"],
                detected_color,
                status,
                roi_detection["detected_hex"],
                roi_detection["standard_hex"],
                roi_detection["detected_rgb"],
                roi_detection["standard_rgb"],
                roi_detection["color_distance"],
                roi_detection["match_standard"],
                roi_detection["color_ratio"],
            )
            event = {
                "product_id": product_id,
                "object_name": roi_detection["object_name"],
                "detected_color": detected_color,
                "detected_color_label": COLOR_LABELS_VI.get(detected_color, detected_color),
                "rgb_value": tuple_to_string(roi_detection["rgb"]),
                "hsv_value": tuple_to_string(roi_detection["hsv"]),
                "standard_hex": roi_detection["standard_hex"],
                "detected_hex": roi_detection["detected_hex"],
                "standard_rgb": roi_detection["standard_rgb"],
                "detected_rgb": roi_detection["detected_rgb"],
                "color_distance": roi_detection["color_distance"],
                "match_standard": roi_detection["match_standard"],
                "color_ratio": roi_detection["color_ratio"],
                "result_hash": result_hash,
                "target_color": self.target_color,
                "confidence": roi_detection["confidence"],
                "status": status,
                "box": roi_detection["box"],
                "center": roi_detection["center"],
                "center_text": roi_detection["center_text"],
                "robot": robot_plan,
                "robot_command": "WAIT_SHOW_COORDS",
                "robot_target_bin": robot_plan["target_bin"],
                "hex": roi_detection["detected_hex"] or COLOR_HEX.get(detected_color, "#64748b"),
                "image_path": None,
            }
            event["robot_serial"] = self.robot_controller._result(False, "show_coordinates_only", "WAIT_SHOW_COORDS")
            events.append(event)

        fps = 1.0 / max(time.perf_counter() - started, 1e-6)
        self._draw_hud(annotated, fps, len(events))
        self.latest_payload = {
            "fps": round(fps, 1),
            "total_objects": len(events),
            "color_counts": dict(color_counter),
            "ignored_count": color_counter.get("ignored", 0),
            "events": events[:20],
            "target_color": self.target_color,
            "confidence": self.confidence,
            "model_status": "ROI color contour",
            "robot_serial": {
                "enabled": self.robot_controller.enabled,
                "status": "show_coordinates_only",
                "port": self.robot_controller.port,
                "error": self.robot_controller.last_error,
            },
        }
        return annotated, self.latest_payload

    def _detect_roi_color_object(self, frame, annotated):
        h, w = frame.shape[:2]

        roi_x1 = int(w * 0.18)
        roi_y1 = int(h * 0.18)
        roi_x2 = int(w * 0.90)
        roi_y2 = int(h * 0.60)

        cv2.rectangle(annotated, (roi_x1, roi_y1), (roi_x2, roi_y2), (0, 255, 255), 2)
        cv2.putText(
            annotated,
            "VUNG NHAN DIEN",
            (roi_x1, roi_y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
        if roi.size == 0:
            return None

        blurred = cv2.GaussianBlur(roi, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        kernel = np.ones((5, 5), np.uint8)
        color_ranges = {
            "red": [((0, 70, 80), (12, 255, 255)), ((170, 70, 80), (179, 255, 255))],
            "yellow": [((18, 45, 90), (42, 255, 255))],
            "blue": [((82, 25, 70), (115, 255, 255))],
        }

        best = None
        roi_area = max((roi_x2 - roi_x1) * (roi_y2 - roi_y1), 1)
        min_area = max(900, int(roi_area * 0.01))
        for color_name, ranges in color_ranges.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in ranges:
                mask = cv2.bitwise_or(mask, cv2.inRange(hsv, np.array(lower), np.array(upper)))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
            cnt = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            if best is None or area > best["area"]:
                best = {"color": color_name, "contour": cnt, "mask": mask, "area": area}

        if best is None:
            return None

        detected_color = best["color"]
        x, y, bw, bh = cv2.boundingRect(best["contour"])

        cx_roi = x + bw // 2
        cy_roi = y + bh // 2

        cx = roi_x1 + cx_roi
        cy = roi_y1 + cy_roi

        x1 = roi_x1 + x
        y1 = roi_y1 + y
        x2 = roi_x1 + x + bw
        y2 = roi_y1 + y + bh

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(annotated, (cx, cy), 5, (255, 255, 255), -1)
        cv2.putText(
            annotated,
            f"{detected_color.upper()} X:{cx} Y:{cy}",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        rgb, hsv_value, detected_hex = self._masked_average_color(blurred, best["mask"])
        return {
            "object_name": "roi_color_block",
            "detected_color": detected_color,
            "box": [x1, y1, x2, y2],
            "center": {"x": cx, "y": cy},
            "center_text": f"{cx},{cy}",
            "confidence": 1.0,
            "rgb": rgb,
            "hsv": hsv_value,
            "standard_hex": COLOR_HEX.get(detected_color, detected_hex),
            "detected_hex": detected_hex,
            "standard_rgb": list(rgb),
            "detected_rgb": list(rgb),
            "color_distance": 0,
            "match_standard": True,
            "color_ratio": round(float(best["area"]) / roi_area, 4),
        }

    def _masked_average_color(self, image, mask):
        mean_bgr = cv2.mean(image, mask=mask)[:3]
        bgr = np.array([[[int(mean_bgr[0]), int(mean_bgr[1]), int(mean_bgr[2])]]], dtype=np.uint8)
        rgb = tuple(int(v) for v in bgr[0][0][::-1])
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[0][0]
        detected_hex = "#{:02X}{:02X}{:02X}".format(*rgb)
        return rgb, tuple(int(v) for v in hsv), detected_hex

    def process_image(self, image_path, output_path=None):
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise ValueError("Khong doc duoc anh upload.")
        annotated, payload = self.process_frame(frame, persist_logs=False, save_defects=False)
        output_path = output_path or Path(OUTPUT_IMAGE_DIR) / f"result_{timestamp_slug()}.jpg"
        cv2.imwrite(str(output_path), annotated)
        payload = dict(payload)
        payload["output_path"] = str(output_path)
        return payload

    def process_video(self, video_path, output_path):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError("Khong doc duoc video upload.")
        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        frame_count = 0
        last_payload = self._empty_payload()
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            annotated, last_payload = self.process_frame(frame, persist_logs=False, save_defects=False)
            writer.write(annotated)
            frame_count += 1
        cap.release()
        writer.release()
        last_payload = dict(last_payload)
        last_payload["frames_processed"] = frame_count
        last_payload["output_path"] = str(output_path)
        return last_payload

    def _draw_detection(self, frame, event):
        x1, y1, x2, y2 = event["box"]
        color_hex = event["hex"].lstrip("#")
        rgb = tuple(int(color_hex[i : i + 2], 16) for i in (0, 2, 4))
        bgr = (rgb[2], rgb[1], rgb[0])
        if event["status"] == "wrong_color":
            bgr = (0, 0, 255)
        elif event["status"] == "ignored":
            bgr = (100, 116, 139)
        cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
        center = event.get("center") or {}
        center_x = int(center.get("x", (x1 + x2) // 2))
        center_y = int(center.get("y", (y1 + y2) // 2))
        cv2.drawMarker(frame, (center_x, center_y), bgr, markerType=cv2.MARKER_CROSS, markerSize=18, thickness=2)
        label = (
            f"{event['object_name']} | {event['detected_color_label']} "
            f"{event['color_ratio']:.2f} | {event['status']}"
        )
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 12)), (x1 + tw + 10, y1), bgr, -1)
        cv2.putText(frame, label, (x1 + 5, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        robot_label = f"C({center_x},{center_y}) | {event.get('robot_command', 'WAIT')}"
        cv2.putText(frame, robot_label, (x1, min(frame.shape[0] - 10, y2 + 22)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, bgr, 2)

    def _draw_hud(self, frame, fps, total):
        text = f"FPS {fps:.1f} | Objects {total}"
        cv2.rectangle(frame, (14, 14), (285, 52), (15, 23, 42), -1)
        cv2.putText(frame, text, (24, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (34, 211, 238), 2)

    def _save_defect_image(self, frame, color):
        OUTPUT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_IMAGE_DIR / f"defect_{color}_{timestamp_slug()}.jpg"
        cv2.imwrite(str(path), frame)
        return str(path)

    def _empty_payload(self):
        return {
            "fps": 0,
            "total_objects": 0,
            "color_counts": {},
            "ignored_count": 0,
            "events": [],
            "target_color": self.target_color,
            "confidence": self.confidence,
            "model_status": "starting",
        }

    def _resolve_status(self, detected_color, color=None):
        if detected_color not in COLOR_NAMES:
            return "ignored"
        if self.target_color and detected_color != self.target_color:
            return "wrong_color"
        return "valid"

    def _should_enqueue_blockchain(self, event):
        return False

    def _make_result_hash(
        self,
        product_id,
        object_name,
        detected_color,
        status,
        detected_hex,
        standard_hex,
        detected_rgb,
        standard_rgb,
        color_distance,
        match_standard,
        color_ratio,
    ):
        payload = {
            "product_id": product_id,
            "object_name": object_name,
            "detected_color": detected_color,
            "status": status,
            "detected_hex": (detected_hex or "").upper(),
            "standard_hex": (standard_hex or "").upper(),
            "detected_rgb": [int(v) for v in (detected_rgb or [])],
            "standard_rgb": [int(v) for v in (standard_rgb or [])],
            "color_distance": None if color_distance is None else round(float(color_distance), 2),
            "match_standard": bool(match_standard),
            "color_ratio": round(float(color_ratio or 0), 4),
        }
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
