from config import COLOR_LABELS_VI, COLOR_NAMES


class RobotArmSimulator:
    def __init__(self):
        self.drop_bins = {
            "red": {"id": "BIN_A", "label": "Red bin", "position": {"x": 80, "y": 180, "z": 40}},
            "yellow": {"id": "BIN_B", "label": "Yellow bin", "position": {"x": 160, "y": 180, "z": 40}},
            "blue": {"id": "BIN_C", "label": "Blue bin", "position": {"x": 240, "y": 180, "z": 40}},
        }

    def create_plan(self, detected_color, box, frame_shape, status):
        center_x, center_y = self._box_center(box)
        robot_x, robot_y = self._image_to_robot(center_x, center_y, frame_shape)

        if detected_color not in COLOR_NAMES or status == "ignored":
            return {
                "enabled": False,
                "mode": "simulation",
                "command": "WAIT_NO_TARGET",
                "display_command": "WAIT",
                "target_bin": None,
                "target_bin_label": None,
                "pick_position": {"x": robot_x, "y": robot_y, "z": 35},
                "drop_position": None,
                "center": {"x": center_x, "y": center_y},
                "center_text": f"{center_x},{center_y}",
                "note": "Object is outside configured colors",
            }

        bin_info = self.drop_bins.get(detected_color)
        color_label = COLOR_LABELS_VI.get(detected_color, detected_color)
        command = f"PICK_{detected_color.upper()}_DROP_{bin_info['id']}"

        return {
            "enabled": True,
            "mode": "simulation",
            "command": command,
            "display_command": command.replace("_", " -> ", 1),
            "target_bin": bin_info["id"],
            "target_bin_label": f"{bin_info['id']} - {color_label}",
            "pick_position": {"x": robot_x, "y": robot_y, "z": 35},
            "drop_position": bin_info["position"],
            "center": {"x": center_x, "y": center_y},
            "center_text": f"{center_x},{center_y}",
            "note": "Simulation only; replace this command with Serial output when the arm is ready",
        }

    def _box_center(self, box):
        x1, y1, x2, y2 = box
        return (int(x1) + int(x2)) // 2, (int(y1) + int(y2)) // 2

    def _image_to_robot(self, center_x, center_y, frame_shape):
        height, width = frame_shape[:2]
        robot_x = round((center_x / max(width, 1)) * 300, 1)
        robot_y = round((center_y / max(height, 1)) * 220, 1)
        return robot_x, robot_y
