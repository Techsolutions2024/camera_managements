# camera_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
from count.roi_manager import load_roi
from count.counting import ObjectCounter
import time
import json
import os
import cv2

class CameraThread(QThread):
    frame_received = pyqtSignal(int, object, int, int, int)

    def __init__(self, cam_id, source, model_path='yolov8x.pt', classes_to_count=[0], threshold=0.25):
        super().__init__()
        self.cam_id = cam_id
        self.source = source
        self.model_path = model_path
        self.classes_to_count = classes_to_count
        self.ai_enabled = False
        self.running = True
        self.counter = None
        self.threshold = threshold
        self.last_save_time = time.time()
        self.save_interval = 10  # Save every 10 seconds

        self.roi_list = load_roi(f"Camera {cam_id}")
        print(f"Loaded ROI for Camera {cam_id}: {self.roi_list}")
        if self.roi_list:
            try:
                self.counter = ObjectCounter(model_path, classes_to_count, self.roi_list, save_interval=self.save_interval, threshold=self.threshold)
                print(f"Initialized ObjectCounter for Camera {cam_id}")
            except ValueError as e:
                print(f"Error initializing ObjectCounter for Camera {cam_id}: {e}")

    def set_ai_enabled(self, enabled):
        self.ai_enabled = enabled

    def save_stats(self):
        if not self.ai_enabled or not self.counter:
            return
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            stats_file = f"stats_data/camera_{self.cam_id}_stats.json"
            os.makedirs("stats_data", exist_ok=True)
            total_counts = self.counter.get_total_counts()
            data = {
                "camera_id": self.cam_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "in": total_counts["in"],
                "out": total_counts["out"],
                "total": total_counts["total"]
            }
            try:
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                stats = []
            stats.append(data)
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=4)
            self.last_save_time = current_time

    def run(self):
        cap = cv2.VideoCapture(self.source)
        while self.running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (640, 480))

                # Tạo bản sao mới của frame gốc để vẽ ROI
                frame_with_counts = frame.copy()

                if self.ai_enabled and self.counter:
                    # Đếm đối tượng và lấy các kết quả đếm
                    frame_with_counts, _ = self.counter.count(frame)
                    total_counts = self.counter.get_total_counts()
                    in_count = total_counts['in']
                    out_count = total_counts['out']
                    total = total_counts['total']
                    self.save_stats()  # Lưu thống kê định kỳ
                else:
                    in_count, out_count, total = 0, 0, 0
                    # Vẽ lại các ROI
                    for line in self.roi_list:
                        if isinstance(line, list) and len(line) == 2:
                            pt1, pt2 = tuple(line[0]), tuple(line[1])  # Chuyển tọa độ ROI thành tuple
                            cv2.line(frame_with_counts, pt1, pt2, (0, 255, 0), 2)  # Vẽ ROI với màu xanh lá

                # Gửi tín hiệu với thông tin frame và các số liệu đếm
                self.frame_received.emit(self.cam_id, frame_with_counts, in_count, out_count, total)
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Đặt lại video nếu hết đoạn
                continue
            self.msleep(30)  # Dừng lại 30ms trước khi tiếp tục
        cap.release()

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
