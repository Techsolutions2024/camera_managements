import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem,
    QGridLayout, QComboBox, QScrollArea
)
import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPixmap
from heatmap.camera_management import CameraManagerDialog
from PyQt5.QtWidgets import QMainWindow
from heatmap.camera_thread import CameraThread  # Import CameraThread class here

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPixmap

class CameraWidget(QWidget):
    def __init__(self, name="Camera", cam_id=None, parent=None):
        super().__init__()
        self.cam_id = cam_id
        self.parent = parent
        self.layout = QVBoxLayout()

        # Camera name label
        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))

        # Video display label
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: #ccc; border: 1px solid #999;")
        self.video_label.setFixedSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)

        # Camera status label
        self.status_label = QLabel("Status: 🟢 Online")
        self.status_label.setStyleSheet("""
            font-size: 10px;
            min-width: 100px;
            max-height: 20px;
            padding: 2px;
        """)

        # Toggle AI heatmap button
        self.ai_toggle_btn = QPushButton("Enable AI Heatmap")
        self.ai_toggle_btn.setCheckable(True)
        self.ai_toggle_btn.clicked.connect(self.toggle_ai_heatmap)

        # Layout for status and button
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.ai_toggle_btn)
        status_layout.addStretch()

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.video_label)
        self.layout.addLayout(status_layout)
        self.setLayout(self.layout)

    def toggle_ai_heatmap(self):
        """Handle toggle button click event."""
        if self.ai_toggle_btn.isChecked():
            self.ai_toggle_btn.setText("Disable AI Heatmap")
            self.parent.camera_threads[self.cam_id].set_ai_heatmap(True)
        else:
            self.ai_toggle_btn.setText("Enable AI Heatmap")
            self.parent.camera_threads[self.cam_id].set_ai_heatmap(False)

class MainWindow(QMainWindow):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window  # Store reference to main window
        self.setWindowTitle("AI HeatMap")
        self.resize(1400, 1000)
        self.setStyleSheet("background-color: #e0f7fa;")

        self.cameras = []  # List of cameras: (cam_id, source)
        self.camera_widgets = {}
        self.camera_labels = {}
        self.camera_threads = {}
        self.current_page = 0
        self.grid_mode = "2x2"

        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Sidebar for navigation
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItem(QListWidgetItem("🟢 Camera trực tiếp"))
        self.sidebar.addItem(QListWidgetItem("📷 Quản lý camera"))
        self.sidebar.addItem(QListWidgetItem("⚙️ Cài đặt"))
        self.sidebar.addItem(QListWidgetItem("🔒 Logout"))
        self.sidebar.addItem(QListWidgetItem("🏠 Quay Lại"))
        self.sidebar.currentRowChanged.connect(self.switch_menu)

        self.pages = QStackedWidget()
        self.camera_page = self.build_camera_page()
        self.pages.addWidget(self.camera_page)
        self.pages.addWidget(QWidget())  # Placeholder
        self.pages.addWidget(QLabel("Software settings."))
        self.pages.addWidget(QLabel("Logout"))

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)

    def start_camera(self, cam_id, source):
        thread = CameraThread(cam_id, source)
        thread.frame_received.connect(self.update_camera_view)
        thread.start()
        self.camera_threads[cam_id] = thread

    def build_camera_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["2x2", "3x3"])
        self.layout_combo.currentTextChanged.connect(self.change_layout)
        control_layout.addWidget(QLabel("Select layout mode:"))
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
        self.page_label.setText(f"Page {self.current_page + 1} / {total_pages}")

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
                widget = CameraWidget(name=f"Camera {cam_id}", cam_id=cam_id, parent=self)
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
        if index == 1:  # Camera management
            dialog = CameraManagerDialog(self)
            dialog.cameras_updated.connect(self.set_camera_sources)
            dialog.exec_()
        elif index == 4:  # Quay Lại
            if self.main_window:
                self.main_window.show()
                self.hide()
        else:
            self.pages.setCurrentIndex(index)

    def set_camera_sources(self, cam_list):
        self.cameras = cam_list
        self.current_page = 0
        self.display_cameras()

    def update_camera_view(self, cam_id, frame):
        """Cập nhật hình ảnh video lên cửa sổ khi có frame mới"""
        if cam_id in self.camera_labels:
            # Chuyển đổi frame thành RGB để PyQt5 có thể hiển thị
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_image.shape
            bytes_per_line = channel * width

            # Chỉ tạo đối tượng QImage và QPixmap khi cần thiết
            q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)

            # Cập nhật frame lên widget video label
            self.camera_labels[cam_id].setPixmap(pixmap.scaled(640, 480, Qt.KeepAspectRatio))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
