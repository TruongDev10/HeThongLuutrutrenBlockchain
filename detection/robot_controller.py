import time

from config import (
    ROBOT_COMMAND_COOLDOWN_SECONDS,
    ROBOT_MIN_COLOR_RATIO,
    ROBOT_MIN_CONFIDENCE,
    ROBOT_SERIAL_BAUDRATE,
    ROBOT_SERIAL_ENABLED,
    ROBOT_SERIAL_PORT,
)


class RobotArmController:
    def __init__(self):
        self.enabled = ROBOT_SERIAL_ENABLED
        self.port = ROBOT_SERIAL_PORT
        self.baudrate = ROBOT_SERIAL_BAUDRATE
        self.cooldown_seconds = ROBOT_COMMAND_COOLDOWN_SECONDS
        self.serial = None
        self.last_command_time = 0.0
        self.last_signature = None
        self.status = "disabled"
        self.last_error = None

        if self.enabled:
            self._connect()

    def _connect(self):
        try:
            import serial

            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2.0)
            self.status = f"connected:{self.port}"
            self.last_error = None
        except Exception as exc:
            self.serial = None
            self.status = "serial_error"
            self.last_error = str(exc)

    def create_command(self, event):
        robot = event.get("robot") or {}
        pick = robot.get("pick_position") or {}
        color = event.get("detected_color")
        status = event.get("status")
        if not robot.get("enabled"):
            return None
        if status not in {"valid", "wrong_color"}:
            return None
        if float(event.get("confidence") or 0) < ROBOT_MIN_CONFIDENCE:
            return None
        if float(event.get("color_ratio") or 0) < ROBOT_MIN_COLOR_RATIO:
            return None
        if pick.get("x") is None or pick.get("y") is None:
            return None

        return f"PICK {float(pick['x']):.1f} {float(pick['y']):.1f} {color} {status}"

    def maybe_execute(self, event):
        command = self.create_command(event)
        if command is None:
            return self._result(False, "no_command", None)

        signature = self._signature(event)
        now = time.time()
        if signature == self.last_signature and now - self.last_command_time < self.cooldown_seconds:
            return self._result(False, "cooldown", command)

        self.last_signature = signature
        self.last_command_time = now

        if not self.enabled:
            return self._result(False, "disabled", command)

        if self.serial is None or not getattr(self.serial, "is_open", False):
            self._connect()
        if self.serial is None:
            return self._result(False, self.status, command)

        try:
            self.serial.write((command + "\n").encode("ascii"))
            self.serial.flush()
            self.status = "sent"
            self.last_error = None
            return self._result(True, "sent", command)
        except Exception as exc:
            self.status = "send_error"
            self.last_error = str(exc)
            return self._result(False, "send_error", command)

    def _signature(self, event):
        center = event.get("center") or {}
        grid_x = round(float(center.get("x", 0)) / 30)
        grid_y = round(float(center.get("y", 0)) / 30)
        return event.get("detected_color"), event.get("status"), grid_x, grid_y

    def _result(self, sent, status, command):
        return {
            "enabled": self.enabled,
            "sent": sent,
            "status": status,
            "command": command,
            "port": self.port,
            "error": self.last_error,
        }
