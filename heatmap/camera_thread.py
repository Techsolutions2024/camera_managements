from PyQt5.QtCore import QThread, pyqtSignal
import cv2
from ultralytics import solutions
import torch

# Đảm bảo mô hình sử dụng GPU (device 0)
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

class CameraThread(QThread):
    frame_received = pyqtSignal(int, object)  # Emitting the frame with camera ID

    def __init__(self, cam_id, source, parent=None):
        super().__init__(parent)
        self.cam_id = cam_id
        self.source = source
        self._ai_heatmap = False  # Default is AI heatmap disabled

    def set_ai_heatmap(self, enabled):
        """Set AI heatmap state for this camera."""
        self._ai_heatmap = enabled

    def run(self):
        cap = cv2.VideoCapture(self.source)
        while True:  # Infinite loop to replay the video
            ret, frame = cap.read()
            if not ret:  # Check if video has finished
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to the first frame to loop
                continue  # Skip the rest of the loop and restart

            # Apply AI heatmap if enabled
            if self._ai_heatmap:
                frame = self.apply_ai_heatmap(frame)

            self.frame_received.emit(self.cam_id, frame)

        cap.release()

    def apply_ai_heatmap(self, frame):
        """Apply AI heatmap to the frame."""
        heatmap = solutions.Heatmap(model="yolo11n.pt", 
                                    colormap=cv2.COLORMAP_PARULA,
                                    conf = 0.2,
                                    device = 0,
                                    classes = [0])
        return heatmap.process(frame).plot_im  # Return the frame with heatmap

