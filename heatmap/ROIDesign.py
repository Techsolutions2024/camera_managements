import cv2
import json
import os
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox, QInputDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint
from heatmap.roi_manager import save_roi, load_roi

class ROIDesign(QWidget):
    def __init__(self, camera_sources: dict):
        super().__init__()
        self.setWindowTitle("Vẽ ROI - Line")
        self.camera_sources = camera_sources
        self.current_camera = None
        # Mỗi ROI là một dict chứa "name", "start" và "end"
        self.lines = []
        self.drawing = False
        self.start_point = QPoint()

        self.init_ui()

    def init_ui(self):
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        self.comboBox = QComboBox()
        self.comboBox.addItems(self.camera_sources.keys())
        self.comboBox.currentTextChanged.connect(self.change_camera)

        btn_save = QPushButton("Lưu ROI")
        btn_clear = QPushButton("Xóa ROI")
        btn_close = QPushButton("Đóng")

        btn_save.clicked.connect(self.save_roi)
        btn_clear.clicked.connect(self.clear_roi)
        btn_close.clicked.connect(self.close)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.comboBox)
        top_bar.addWidget(btn_save)
        top_bar.addWidget(btn_clear)
        top_bar.addWidget(btn_close)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.change_camera(self.comboBox.currentText())

    def change_camera(self, camera_name):
        self.current_camera = camera_name
        self.cap = cv2.VideoCapture(self.camera_sources[camera_name])
        # Load ROI đã lưu nếu có
        self.lines = load_roi(camera_name)
        self.update_frame()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.label.mapFromGlobal(event.globalPos())
            self.start_point = (pos.x(), pos.y())
            self.drawing = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            pos = self.label.mapFromGlobal(event.globalPos())
            end_point = (max(0, min(pos.x(), 640)), max(0, min(pos.y(), 480)))
            self.start_point = (max(0, min(self.start_point[0], 640)), max(0, min(self.start_point[1], 480)))
            roi_name, ok = QInputDialog.getText(self, "Nhập tên ROI", "Tên ROI:")
            if not ok or not roi_name.strip():
                roi_name = f"ROI {len(self.lines)+1}"
            self.lines.append({
                "name": roi_name,
                "start": [self.start_point[0], self.start_point[1]],
                "end": [end_point[0], end_point[1]]
            })
            self.drawing = False
            self.update_frame()

    def paint_lines(self, image):
        print(f"Frame size: {image.shape}")
        for i, line in enumerate(self.lines):
            start = tuple(line["start"])
            end = tuple(line["end"])
            print(f"ROI {line['name']}: start={start}, end={end}")
            cv2.line(image, start, end, (0, 255, 0), 2)
            mid_point = (int((start[0] + end[0]) / 2), int((start[1] + end[1]) / 2))
            roi_name = line.get("name", f"ROI {i+1}")
            cv2.putText(image, roi_name, mid_point, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


    def update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # Resize frame để phù hợp với UI (640x480)
        frame = cv2.resize(frame, (640, 480))
        self.paint_lines(frame)

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_image.shape
        bytes_per_line = channel * width
        q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.label.setPixmap(pixmap)

    def save_roi(self):
        if not self.current_camera:
            return
        save_roi(self.current_camera, self.lines)
        QMessageBox.information(self, "Lưu ROI", "Đã lưu thành công!")

    def clear_roi(self):
        self.lines = []
        self.update_frame()
