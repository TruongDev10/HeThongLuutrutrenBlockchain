COLOR_CONFIG = {
    "red": {
        "name": "red",
        "vi_name": "Do",
        "hex": "#D7352E",
        "rgb": (215, 53, 46),
        "hsl": (3, 65, 51),
        "cmyk": (0, 75, 79, 16),
        "hsv_ranges": [((0, 70, 80), (12, 255, 255)), ((170, 70, 80), (179, 255, 255))],
        "tolerance": 80,
    },
    "yellow": {
        "name": "yellow",
        "vi_name": "Vang",
        "hex": "#D8C65D",
        "rgb": (216, 198, 93),
        "hsl": (51, 62, 61),
        "cmyk": (0, 8, 57, 15),
        "hsv_ranges": [((18, 45, 90), (42, 255, 255))],
        "tolerance": 85,
    },
    "blue": {
        "name": "blue",
        "vi_name": "Xanh duong",
        "hex": "#58AFD1",
        "rgb": (88, 175, 209),
        "hsl": (197, 57, 58),
        "cmyk": (58, 16, 0, 18),
        "hsv_ranges": [((85, 35, 90), (110, 255, 255))],
        "tolerance": 85,
    },
}

TARGET_COLOR_NAMES = list(COLOR_CONFIG.keys())
NOT_TARGET_COLOR = "not_target_color"
IGNORED_COLOR = "ignored"
MIN_COLOR_RATIO = 0.18
CENTER_CROP_MARGIN_RATIO = 0.08
