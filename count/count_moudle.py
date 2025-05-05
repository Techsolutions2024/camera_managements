import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem,
    QGridLayout, QComboBox, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPixmap
from count.camera_management import CameraManagerDialog
from count.camera_thread import CameraThread
import cv2
import os
from count.ROIDesign import ROIDesign
from count.roi_manager import load_roi
from count.statistic_view import StatisticsView  # Import StatisticsView từ statistic_view.py

class CameraWidget(QWidget):
    def __init__(self, name="Camera", in_count=0, out_count=0, total=0):
        super().__init__()
        self.layout = QVBoxLayout()

        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: #ccc; border: 1px solid #999;")
        self.video_label.setFixedSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.status_label = QLabel("Trạng thái: 🟢 Online")
        self.status_label.setStyleSheet("""
            font-size: 10px;
            min-width: 100px;
            max-height: 20px;
            padding: 2px;
        """)

        self.ai_button = QPushButton("Bật AI")
        self.ai_button.setCheckable(True)
        self.ai_button.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                min-width: 50px;
                max-height: 20px;
                padding: 2px;
                background-color: red;
            }
            QPushButton:checked {
                background-color: green;
            }
        """)
        self.ai_button.clicked.connect(self.toggle_ai)

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.ai_button)
        status_layout.addStretch()

        self.info_label = QLabel(f"IN: {in_count} | OUT: {out_count} | TOTAL: {total}")

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.video_label)
        self.layout.addLayout(status_layout)
        self.layout.addWidget(self.info_label)
        self.setLayout(self.layout)

        self.ai_enabled = False

    def toggle_ai(self):
        self.ai_enabled = not self.ai_enabled
        if self.ai_enabled:
            self.ai_button.setText("Tắt AI")
        else:
            self.ai_button.setText("Bật AI")

class MainWindow(QMainWindow):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window  # Store reference to main window
        self.setWindowTitle("AI People Counter")
        self.resize(1400, 1000)
        self.setStyleSheet("background-color: #e0f7fa;")

        self.cameras = []              # Danh sách các camera, mỗi phần tử là tuple (cam_id, source)
        self.camera_widgets = {}
        self.camera_labels = {}
        self.camera_threads = {}
        self.current_page = 0
        self.grid_mode = "2x2"
        self.camera_rois = {}
        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Sidebar điều hướng
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItem(QListWidgetItem("🟢 Camera trực tiếp"))
        self.sidebar.addItem(QListWidgetItem("📈 Biểu đồ thống kê"))
        self.sidebar.addItem(QListWidgetItem("🧠 ROI / AI"))
        self.sidebar.addItem(QListWidgetItem("📄 Xuất báo cáo"))
        self.sidebar.addItem(QListWidgetItem("📷 Quản lý camera"))
        self.sidebar.addItem(QListWidgetItem("⚙️ Cài đặt"))
        self.sidebar.addItem(QListWidgetItem("🏠 Quay Lại"))
        self.sidebar.currentRowChanged.connect(self.switch_menu)

        self.pages = QStackedWidget()
        self.camera_page = self.build_camera_page()
        
        self.pages.addWidget(self.camera_page)
        
        # Thêm StatisticsView thay vì placeholder
        self.statistics_page = StatisticsView()
        self.pages.addWidget(self.statistics_page)  # Index 1
        
        self.pages.addWidget(QLabel("Chức năng ROI và AI xử lý tại đây."))
        self.pages.addWidget(QLabel("Báo cáo PDF / Excel xuất tại đây."))
        self.pages.addWidget(QWidget())
        self.pages.addWidget(QLabel("Cài đặt phần mềm."))
        self.pages.addWidget(QLabel("Đăng xuất"))

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)

    def load_rois(self, cam_id):
        roi_list = load_roi(f"Camera {cam_id}")
        self.camera_rois[cam_id] = roi_list
        
    def open_roi_design_window(self):
        if not self.cameras:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có camera nào. Vui lòng thêm camera từ mục '📷 Quản lý camera'.")
            return

        camera_sources = {}
        for cam in self.cameras:
            cam_id, source = cam
            camera_name = f"Camera {cam_id}"
            camera_sources[camera_name] = source

        self.roi_window = ROIDesign(camera_sources)
        self.roi_window.show()

    def build_camera_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["2x2", "3x3"])
        self.layout_combo.currentTextChanged.connect(self.change_layout)
        control_layout.addWidget(QLabel("Chọn chế độ hiển thị:"))
        control_layout.addWidget(self.layout_combo)

        self.page_label = QLabel()
        self.update_page_label()

        prev_button = QPushButton("⬅️")
        prev_button.clicked.connect(self.prev_page)
        next_button = QPushButton("➡️")
        next_button.clicked.connect(self.next_page)

        control_layout.addStretch()
        control_layout.addWidget(prev_button)
        control_layout.addWidget(self.page_label)
        control_layout.addWidget(next_button)

        layout.addLayout(control_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.scroll_area.setAlignment(Qt.AlignHCenter)
        self.grid_layout = QGridLayout()
        self.grid_container.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)

        page.setLayout(layout)
        return page

    def update_page_label(self):
        total = len(self.cameras)
        per_page = 4 if self.grid_mode == "2x2" else 9
        total_pages = max(1, (total + per_page - 1) // per_page)
        self.page_label.setText(f"Trang {self.current_page + 1} / {total_pages}")

    def display_cameras(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        per_page = 4 if self.grid_mode == "2x2" else 9
        start = self.current_page * per_page
        end = min(start + per_page, len(self.cameras))

        num_cols = 2 if self.grid_mode == "2x2" else 3
        for i, (cam_id, source) in enumerate(self.cameras[start:end]):
            row = i // num_cols
            col = i % num_cols
            if cam_id not in self.camera_widgets:
                widget = CameraWidget(name=f"Camera {cam_id}")
                self.camera_widgets[cam_id] = widget
                self.camera_labels[cam_id] = widget.video_label
                self.start_camera(cam_id, source)
            self.grid_layout.addWidget(self.camera_widgets[cam_id], row, col)

        self.update_page_label()

    def change_layout(self, text):
        self.grid_mode = text
        self.current_page = 0
        self.display_cameras()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_cameras()

    def next_page(self):
        per_page = 4 if self.grid_mode == "2x2" else 9
        max_page = (len(self.cameras) + per_page - 1) // per_page
        if self.current_page + 1 < max_page:
            self.current_page += 1
            self.display_cameras()

    def switch_menu(self, index):
        if index == 4:
            dialog = CameraManagerDialog(self)
            dialog.cameras_updated.connect(self.set_camera_sources)
            dialog.exec_()
        elif index == 2:  # ROI / AI
            self.open_roi_design_window()
        elif index == 6:  # Quay Lại
            if self.main_window:
                self.main_window.show()
                self.hide()
        else:
            self.pages.setCurrentIndex(index)

    def set_camera_sources(self, cam_list):
        self.cameras = cam_list
        self.current_page = 0
        self.display_cameras()

    def start_camera(self, cam_id, source):
        thread = CameraThread(cam_id, source, model_path='yolo11n.pt', classes_to_count=[0])  # [0] là class "person"
        thread.frame_received.connect(self.update_camera_view)
        thread.start()
        self.camera_threads[cam_id] = thread
        self.load_rois(cam_id)

        self.camera_widgets[cam_id].ai_button.clicked.connect(
            lambda checked: thread.set_ai_enabled(self.camera_widgets[cam_id].ai_enabled)
        )

    def update_camera_view(self, cam_id, frame, in_count=0, out_count=0, total=0):
        if cam_id in self.camera_rois:
            resized_frame = frame  # Frame đã là 640x480 từ CameraThread
            for roi in self.camera_rois[cam_id]:
                if "start" in roi and "end" in roi:
                    start_x = int(roi['start'][0])
                    start_y = int(roi['start'][1])
                    end_x = int(roi['end'][0])
                    end_y = int(roi['end'][1])
                    cv2.line(resized_frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
                    if 'name' in roi:
                        mid_x = int((start_x + end_x) / 2)
                        mid_y = int((start_y + end_y) / 2)
                        cv2.putText(resized_frame, roi['name'], (mid_x, mid_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            image = QImage(rgb.data, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            if cam_id in self.camera_labels:
                self.camera_labels[cam_id].setPixmap(pixmap)
                self.camera_widgets[cam_id].info_label.setText(f"IN: {in_count} | OUT: {out_count} | TOTAL: {total}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())