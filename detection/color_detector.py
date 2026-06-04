import importlib.util
import math
from pathlib import Path

import cv2
import numpy as np

from config import BASE_DIR


def _load_color_config():
    path = Path(BASE_DIR) / "config" / "colors.py"
    spec = importlib.util.spec_from_file_location("target_color_config", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.COLOR_CONFIG, module.MIN_COLOR_RATIO, module.CENTER_CROP_MARGIN_RATIO


COLOR_CONFIG, MIN_COLOR_RATIO, CENTER_CROP_MARGIN_RATIO = _load_color_config()


class ColorDetector:
    def __init__(self):
        self.kernel = np.ones((5, 5), np.uint8)

    def detect(self, roi):
        if roi is None or roi.size == 0:
            return self._not_target()

        roi = self._center_crop(roi, CENTER_CROP_MARGIN_RATIO)
        if roi is None or roi.size == 0:
            return self._not_target()

        blurred = cv2.GaussianBlur(roi, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        masks, scores = self._target_color_scores(hsv)
        dominant_color = max(scores, key=scores.get) if scores else "not_target_color"
        color_ratio = float(scores.get(dominant_color, 0))

        if color_ratio < MIN_COLOR_RATIO:
            rgb, hsv_value = self._average_rgb_hsv(blurred)
            result = self._not_target()
            result.update(
                {
                    "rgb": rgb,
                    "hsv": hsv_value,
                    "detected_rgb": list(rgb),
                    "detected_hex": self._rgb_to_hex(rgb),
                    "average_rgb": list(rgb),
                    "average_hex": self._rgb_to_hex(rgb),
                    "average_hsv": list(hsv_value),
                    "color_ratio": color_ratio,
                    "score": color_ratio,
                    "distribution": {key: round(float(value), 4) for key, value in scores.items()},
                }
            )
            return result

        mask = masks[dominant_color]
        rgb, hsv_value = self._average_rgb_hsv(blurred, mask)
        cfg = COLOR_CONFIG[dominant_color]
        standard_rgb = tuple(cfg["rgb"])
        distance = self._euclidean_rgb(rgb, standard_rgb)
        match_standard = distance <= float(cfg["tolerance"])

        return {
            "name": dominant_color,
            "vi_name": cfg["vi_name"],
            "label": cfg["vi_name"],
            "standard_hex": cfg["hex"],
            "hex": self._rgb_to_hex(rgb),
            "detected_hex": self._rgb_to_hex(rgb),
            "standard_rgb": list(standard_rgb),
            "detected_rgb": list(rgb),
            "average_rgb": list(rgb),
            "average_hex": self._rgb_to_hex(rgb),
            "average_hsv": list(hsv_value),
            "rgb": rgb,
            "hsv": hsv_value,
            "color_distance": round(distance, 2),
            "match_standard": bool(match_standard),
            "color_ratio": round(color_ratio, 4),
            "score": color_ratio,
            "status": "valid",
            "distribution": {key: round(float(value), 4) for key, value in scores.items()},
        }

    def _center_crop(self, image, margin_ratio):
        h, w = image.shape[:2]
        x1, y1 = int(w * margin_ratio), int(h * margin_ratio)
        x2, y2 = int(w * (1 - margin_ratio)), int(h * (1 - margin_ratio))
        return image[y1:y2, x1:x2] if x2 > x1 and y2 > y1 else image

    def _target_color_scores(self, hsv):
        total = hsv.shape[0] * hsv.shape[1]
        masks = {}
        scores = {}
        for color, config in COLOR_CONFIG.items():
            mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for lower, upper in config["hsv_ranges"]:
                mask_total = cv2.bitwise_or(mask_total, cv2.inRange(hsv, np.array(lower), np.array(upper)))
            mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, self.kernel)
            mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, self.kernel)
            masks[color] = mask_total
            scores[color] = cv2.countNonZero(mask_total) / max(total, 1)
        return masks, scores

    def _average_rgb_hsv(self, image, mask=None):
        if mask is not None and cv2.countNonZero(mask) > 0:
            mean_bgr = cv2.mean(image, mask=mask)[:3]
        else:
            mean_bgr = cv2.mean(image)[:3]
        bgr = np.array([[[int(mean_bgr[0]), int(mean_bgr[1]), int(mean_bgr[2])]]], dtype=np.uint8)
        rgb = tuple(int(v) for v in bgr[0][0][::-1])
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[0][0]
        return rgb, tuple(int(v) for v in hsv)

    def _euclidean_rgb(self, rgb, standard_rgb):
        return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(rgb, standard_rgb)))

    def _rgb_to_hex(self, rgb):
        return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def _not_target(self):
        return {
            "name": "not_target_color",
            "vi_name": "Không thuộc màu mục tiêu",
            "label": "Không thuộc màu mục tiêu",
            "standard_hex": None,
            "hex": "#64748B",
            "detected_hex": "#64748B",
            "standard_rgb": None,
            "detected_rgb": [0, 0, 0],
            "average_rgb": [0, 0, 0],
            "average_hex": "#000000",
            "average_hsv": [0, 0, 0],
            "rgb": (0, 0, 0),
            "hsv": (0, 0, 0),
            "color_distance": None,
            "match_standard": False,
            "color_ratio": 0.0,
            "score": 0.0,
            "status": "ignored",
            "distribution": {},
        }
