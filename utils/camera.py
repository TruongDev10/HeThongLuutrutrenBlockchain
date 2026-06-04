import threading
import time

import cv2

from config import CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH


class CameraStream:
    def __init__(self, camera_index=CAMERA_INDEX):
        self.camera_index = camera_index
        self.capture = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        self.last_error = None
        self.last_frame_time = None

    def start(self):
        if self.running:
            return
        self.capture = self._open_capture(self.camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.capture.isOpened():
            self.capture.release()
            self.capture = None
            self.last_error = "Khong mo duoc camera. Kiem tra webcam/USB camera hoac CAMERA_INDEX."
            raise RuntimeError(self.last_error)
        self.last_error = None
        self.running = True
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()
        deadline = time.time() + 2.0
        while time.time() < deadline:
            with self.lock:
                if self.frame is not None:
                    return
            time.sleep(0.03)
        self.last_error = "Camera da mo nhung chua tra frame. Thu Camera 0/1 hoac dong app dang dung webcam."

    def _open_capture(self, camera_index):
        backends = []
        backends.append(0)
        if hasattr(cv2, "CAP_DSHOW"):
            backends.append(cv2.CAP_DSHOW)
        for backend in backends:
            capture = cv2.VideoCapture(camera_index, backend) if backend else cv2.VideoCapture(camera_index)
            if capture.isOpened():
                return capture
            capture.release()
        return cv2.VideoCapture(camera_index)

    def _reader(self):
        while self.running and self.capture is not None:
            ok, frame = self.capture.read()
            if ok:
                with self.lock:
                    self.frame = frame
                    self.last_frame_time = time.time()
                self.last_error = None
            else:
                self.last_error = "Camera khong doc duoc frame."
                time.sleep(0.03)

    def read(self):
        if not self.running:
            self.start()
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def set_source(self, camera_index):
        camera_index = int(camera_index)
        if camera_index == self.camera_index and self.running:
            return
        self.stop()
        self.camera_index = camera_index
        self.start()

    def status(self):
        with self.lock:
            has_frame = self.frame is not None
        return {
            "camera_index": self.camera_index,
            "running": self.running,
            "error": self.last_error,
            "has_frame": has_frame,
            "last_frame_time": self.last_frame_time,
        }

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        if self.capture is not None:
            self.capture.release()
        self.capture = None
        self.frame = None
        self.last_frame_time = None
