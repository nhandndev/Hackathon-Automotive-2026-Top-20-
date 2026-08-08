import cv2
import numpy as np

class WebcamDriverSource:
    def __init__(self, camera_index: int):
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            # Try without DSHOW if it fails
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Could not open webcam {camera_index}")

    def read_frame(self, frame_id: int) -> np.ndarray:
        # Ignore frame_id for webcam, just grab the latest
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read from webcam")
        return frame

    def close(self):
        self.cap.release()

class DatasetDriverSource:
    def __init__(self, dataset):
        self.dataset = dataset

    def read_frame(self, frame_id: int) -> np.ndarray:
        return self.dataset.load_driver(frame_id)

    def close(self):
        pass
