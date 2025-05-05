import cv2
import threading
import time
import os
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
import numpy as np

class CameraThread(QThread):
    frame_updated = pyqtSignal(QPixmap)
    info_updated = pyqtSignal(str)  # Signal để cập nhật thông tin bitrate và thời gian

    def __init__(self, camera, video_label, info_label, video_label_size, parent=None):
        super().__init__(parent)
        self.paused = False
        self.camera = camera
        self.video_label_size = video_label_size
        self.video_label = video_label
        self.info_label = info_label
        self.capture = None
        self.is_recording = False
        self.recording_writer = None
        self.snapshot_count = 0
        self.start_time = None
        self.duration = 0
        self.bitrate = 0
        self.video_file = None
        self.lock = threading.Lock()

    def run(self):
        """Bắt đầu quá trình capture video và xử lý các frame."""
        self.capture = cv2.VideoCapture(self.camera['source'])
        self.capture.set(cv2.CAP_PROP_FPS, 15)  # Giới hạn FPS
        
        if not self.capture.isOpened():
            QMessageBox.warning(None, "Lỗi", f"Không thể mở camera: {self.camera['name']}")
            return

        self.start_time = time.time()

        while self.capture.isOpened():
            if self.paused:
                time.sleep(0.1)
                continue
            ret, frame = self.capture.read()
            if not ret:
                break

            self.process_frame(frame)

            # Tính toán bitrate và thời gian stream
            self.calculate_stream_info()

            # Cập nhật thông tin label
            self.info_updated.emit(f"Bitrate: {self.bitrate} kbps | Duration: {self.format_duration(self.duration)}")

            # Gửi frame hiện tại để hiển thị
            self.frame_updated.emit(self.convert_frame_to_qpixmap(frame))

            time.sleep(0.05)  # Dừng để tránh quá tải CPU
            
        self.capture.release()

    def process_frame(self, frame):
        """Xử lý frame (chuyển đổi màu sắc, ghi nếu cần)."""
        if self.is_recording:
            self.record_frame(frame)



    def convert_frame_to_qpixmap(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        #return pixmap.scaled(self.video_label_size, Qt.KeepAspectRatio)
        return pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio)



    def calculate_stream_info(self):
        """Tính toán bitrate và thời gian của stream."""
        self.duration = time.time() - self.start_time
        frame_rate = self.capture.get(cv2.CAP_PROP_FPS)
        frame_size = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH) * self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT) * 3
        self.bitrate = (frame_rate * frame_size) / 1000  # tính bitrate (kbps)

    def format_duration(self, duration):
        """Định dạng thời gian stream theo định dạng HH:MM:SS."""
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"


    def start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True

        record_dir = os.path.join("recordings", f"camera_{self.camera['id']}")
        os.makedirs(record_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        #self.video_file = os.path.join(record_dir, f"{timestamp}.mp4")
        self.video_file = os.path.join(record_dir, f"{timestamp}.avi")
        #fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        frame_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.recording_writer = cv2.VideoWriter(self.video_file, fourcc, fps, (frame_width, frame_height))

    def stop_recording(self):
        """Dừng ghi video."""
        if not self.is_recording:
            return

        self.is_recording = False
        if self.recording_writer:
            self.recording_writer.release()
        self.recording_writer = None

    def record_frame(self, frame):
        """Ghi lại frame hiện tại vào file."""
        if self.recording_writer:
            self.recording_writer.write(frame)

        
    def snapshot(self):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                snapshot_dir = "snapshots"
                if not os.path.exists(snapshot_dir):
                    os.makedirs(snapshot_dir)

                snapshot_filename = os.path.join(snapshot_dir, f"snapshot_{self.camera['id']}_{self.snapshot_count}.png")
                cv2.imwrite(snapshot_filename, frame)
                self.snapshot_count += 1


    def pause_stream(self, pause):
        self.paused = pause

    def close(self):
        """Dừng thread và giải phóng tài nguyên."""
        if self.capture:
            self.capture.release()
