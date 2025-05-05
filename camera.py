import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem,
    QGridLayout, QComboBox, QScrollArea, QLineEdit, QDateTimeEdit, QTableWidget,
    QTableWidgetItem, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
from modulecam.camera_manager import CameraManagerDialog
#from main import MainWindow
from datetime import datetime       
from modulecam.camera_thread import CameraThread  # Đảm bảo đã import ở đầu file
import os
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl
import humanize  # pip install humanize
import json
from PyQt5.QtCore import QSize
class CameraPlaceholderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("❌ Không kết nối")
        self.label.setAlignment(Qt.AlignCenter)
        self.setFixedSize(640, 640)

        self.label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px dashed #ccc;
            border-radius: 5px;
        """)

class CameraWidget(QWidget):
    def __init__(self, name="Camera", cam_id=1, camera_data=None):
        super().__init__()
        self.cam_id = cam_id
        self.camera_data = camera_data
        self.layout = QVBoxLayout()

        # Tên camera
        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))

        # Khu vực hiển thị video
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: #ccc; border: 1px solid #999;")
        self.video_label.setFixedSize(640, 640)
        #self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("Đang kết nối...")

        # Trạng thái và điều khiển
        self.status_label = QLabel("🟢 Đang phát")
        self.status_label.setStyleSheet("font-size: 10px; padding: 2px;")

        self.play_button = QPushButton("Pause")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.toggle_pause)

        self.record_button = QPushButton("Record")
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self.toggle_record)

        self.snapshot_button = QPushButton("Snapshot")
        self.snapshot_button.clicked.connect(self.take_snapshot)

        self.zoom_button = QPushButton("Zoom")
        self.zoom_button.setCheckable(True)
        self.zoom_button.clicked.connect(self.toggle_zoom)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.status_label)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.record_button)
        control_layout.addWidget(self.snapshot_button)
        control_layout.addWidget(self.zoom_button)
        control_layout.addStretch()

        # Thông tin luồng
        self.info_label = QLabel("Bitrate: -- | Duration: --")

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.video_label)
        self.layout.addLayout(control_layout)
        self.layout.addWidget(self.info_label)
        self.setLayout(self.layout)

        # Khởi động CameraThread
        if self.camera_data:
            #self.thread = CameraThread(self.camera_data, self.video_label, self.info_label)
            self.thread = CameraThread(self.camera_data, self.video_label, self.info_label, self.video_label.size())
            self.thread.frame_updated.connect(self.update_frame)
            self.thread.info_updated.connect(self.update_info)
            self.thread.start()

    def update_frame(self, pixmap):
        self.video_label.setPixmap(pixmap)

    def update_info(self, info_text):
        self.info_label.setText(info_text)

    def toggle_pause(self):
        if hasattr(self.thread, 'pause_stream'):
            if self.play_button.isChecked():
                self.play_button.setText("Resume")
                self.status_label.setText("⏸️ Tạm dừng")
                self.thread.pause_stream(True)
            else:
                self.play_button.setText("Pause")
                self.status_label.setText("🟢 Đang phát")
                self.thread.pause_stream(False)

    def toggle_record(self):
        if self.record_button.isChecked():
            self.status_label.setText("⏺️ Đang ghi")
            self.thread.start_recording()
        else:
            self.status_label.setText("🟢 Đang phát")
            self.thread.stop_recording()

    def take_snapshot(self):
        self.thread.snapshot()

    def toggle_zoom(self):
        if self.zoom_button.isChecked():
            new_size = QSize(1080, 720)
            self.video_label.setFixedSize(new_size)
            self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.status_label.setText("🔍 Zoomed")
        else:
            new_size = QSize(640, 640)
            self.video_label.setFixedSize(new_size)
            self.video_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.status_label.setText("🟢 Đang phát")

        # Cập nhật kích thước render trong thread
        if hasattr(self.thread, "update_display_size"):
            self.thread.update_display_size(new_size)

    def keyPressEvent(self, event):
        if event.key() == ord('C') or event.key() == ord('c'):
            if self.zoom_button.isChecked():
                self.zoom_button.setChecked(False)
                self.toggle_zoom()
        super().keyPressEvent(event)



class MainWindow(QMainWindow):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window  # Store reference to main window
        self.setWindowTitle("Camera Management System")
        self.resize(1400, 1200)
        # Đặt màu nền
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f4f8;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
            }
            QScrollArea {
                background-color: #f8f9fa;
            }
        """)

        self.current_page = 0
        self.grid_mode = "2x2"
        self.cameras = []
        
        # Layout chính
        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Sidebar điều hướng
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
            }
            QListWidget::item {
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #45a049;
            }
        """)
        self.sidebar.addItem(QListWidgetItem("📹 Stream Video"))
        self.sidebar.addItem(QListWidgetItem("🔍 Tìm kiếm Video"))
        self.sidebar.addItem(QListWidgetItem("📋 Quản lý Camera"))
        self.sidebar.addItem(QListWidgetItem("📂 Xem lại Video"))
        self.sidebar.addItem(QListWidgetItem("🏠 Quay Lại"))
        

        self.sidebar.currentRowChanged.connect(self.switch_menu)

        # Các trang
        
        self.pages = QStackedWidget()
        self.stream_page = self.build_stream_page()
        self.search_page = self.build_search_page()
        self.pages.addWidget(self.stream_page)
        self.pages.addWidget(self.search_page)
        self.review_page = self.build_review_page()
        self.pages.addWidget(self.review_page)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)
        
        
    def save_state(self):
        """Lưu trạng thái của ứng dụng (camera, layout, etc.)"""
        with open('state.json', 'w') as f:
            json.dump(self.cameras, f)

    def load_state(self):
        """Tải lại trạng thái khi quay lại"""
        try:
            with open('state.json', 'r') as f:
                cameras = json.load(f)
                self.display_cameras()
                return cameras
        except FileNotFoundError:
            return []  # Nếu không có trạng thái trước đó, khởi tạo lại danh sách camera

    def reset_data(self):
        """Reset lại dữ liệu và trạng thái của ứng dụng"""
        self.cameras = []
        self.display_cameras()  # Hiển thị lại danh sách camera trống
        self.connection_status.setText("Trạng thái: Chưa kết nối camera")

    def back_to_main(self):
        """Quay lại màn hình chính và lưu trạng thái"""
        self.save_state()  # Lưu trạng thái khi quay lại
        self.show()  # Hiển thị lại giao diện chính
        self.hide()  # Ẩn màn hình hiện tại

    def closeEvent(self, event):
        """Xử lý khi cửa sổ bị đóng"""
        self.reset_data()  # Reset dữ liệu trước khi đóng
        event.accept()  # Đóng cửa sổ



    def build_stream_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # Layout control section
        control_layout = QHBoxLayout()
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["2x2", "3x3"])
        self.layout_combo.currentTextChanged.connect(self.change_layout)
        control_layout.addWidget(QLabel("Chọn chế độ hiển thị:"))
        control_layout.addWidget(self.layout_combo)

        # Add connection status label
        self.connection_status = QLabel("Trạng thái: Chưa kết nối camera")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.connection_status)

        # Page navigation
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

        # Camera grid area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_container.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)

        # Initialize empty camera slots
        self.initialize_empty_slots()

        page.setLayout(layout)
        return page

    def initialize_empty_slots(self):
        """Create empty camera slots with connection status"""
        num_slots = 4 if self.grid_mode == "2x2" else 9
        
        for i in range(num_slots):
            row = i // 2 if self.grid_mode == "2x2" else i // 3
            col = i % 2 if self.grid_mode == "2x2" else i % 3
            
            slot = QWidget()
            slot.setStyleSheet("""
                background-color: #f0f0f0;
                border: 2px dashed #ccc;
                border-radius: 5px;
            """)
            
            status = QLabel("❌ Không kết nối")
            status.setAlignment(Qt.AlignCenter)
            status.setStyleSheet("color: red; font-weight: bold;")
            
            layout = QVBoxLayout()
            layout.addWidget(status)
            slot.setLayout(layout)
            
            self.grid_layout.addWidget(slot, row, col)

    def update_connection_status(self):
        if len(self.cameras) > 0:
            self.connection_status.setText(f"Trạng thái: Đã kết nối {len(self.cameras)} camera")
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_status.setText("Trạng thái: Chưa kết nối camera")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
    

    def build_search_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm theo tên camera hoặc từ khóa")
        self.live_search_checkbox = QComboBox()
        self.live_search_checkbox.addItems(["Video đã lưu", "Đang phát trực tiếp"])
        search_button = QPushButton("Tìm kiếm")
        search_button.clicked.connect(self.search_videos)
        search_layout.addWidget(QLabel("Từ khóa:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.live_search_checkbox)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["Camera", "Folder", "Date", "Event", "Video File"])
        self.result_table.setRowCount(0)
        self.result_table.cellDoubleClicked.connect(self.play_search_result)
        self.search_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.search_video_widget = QVideoWidget()
        self.search_player.setVideoOutput(self.search_video_widget)
        layout.addWidget(self.result_table)
        video_layout = QHBoxLayout()
        video_layout.addStretch()
        video_layout.addWidget(self.search_video_widget)
        video_layout.addStretch()
        layout.addLayout(video_layout)
        self.live_results_layout = QGridLayout()
        live_results_container = QHBoxLayout()
        live_results_container.addStretch()
        live_results_container.addLayout(self.live_results_layout)
        live_results_container.addStretch()
        layout.addLayout(live_results_container)
        page.setLayout(layout)
        return page

    def search_videos(self):
        keyword = self.search_input.text().lower()
        search_mode = self.live_search_checkbox.currentText()
        self.result_table.setRowCount(0)
        if search_mode == "Đang phát trực tiếp":
            self.clear_live_results()
            matched = [cam for cam in self.cameras if keyword in cam["name"].lower() or keyword in str(cam["id"])]
            for i, cam in enumerate(matched):
                widget = CameraWidget(name=cam["name"], cam_id=cam["id"], camera_data=cam)
                row = i // 3
                col = i % 3
                self.live_results_layout.addWidget(widget, row, col)
        else:
            from datetime import datetime
            base_dir = "recordings"
            if not os.path.exists(base_dir):
                return
            row = 0
            for camera_folder in os.listdir(base_dir):
                cam_id = camera_folder.replace("camera_", "")
                folder_path = os.path.join(base_dir, camera_folder)
                for filename in os.listdir(folder_path):
                    if not filename.endswith((".mp4", ".avi")):
                        continue
                    filepath = os.path.join(folder_path, filename)
                    file_stat = os.stat(filepath)
                    created_time = datetime.fromtimestamp(file_stat.st_mtime)
                    if keyword not in filename.lower() and keyword not in cam_id.lower() and keyword not in camera_folder.lower():
                        continue
                    filesize = humanize.naturalsize(file_stat.st_size)
                    created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
                    event = filename.split('_')[0]
                    self.result_table.insertRow(row)
                    self.result_table.setItem(row, 0, QTableWidgetItem(cam_id))
                    self.result_table.setItem(row, 1, QTableWidgetItem(camera_folder))
                    self.result_table.setItem(row, 2, QTableWidgetItem(created_str))
                    self.result_table.setItem(row, 3, QTableWidgetItem(event))
                    self.result_table.setItem(row, 4, QTableWidgetItem(filename))
                    row += 1

    def clear_live_results(self):
        for i in reversed(range(self.live_results_layout.count())):
            widget = self.live_results_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def play_search_result(self, row, col):
        filename = self.result_table.item(row, 4).text()
        cam_id = self.result_table.item(row, 0).text()
        filepath = os.path.join("recordings", f"camera_{cam_id}", filename)
        if os.path.exists(filepath):
            self.search_video_widget.setFixedSize(640, 640)
            self.search_player.setMedia(QMediaContent(QUrl.fromLocalFile(filepath)))
            self.search_player.play()


    def build_manage_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # Danh sách camera
        self.camera_table = QTableWidget()
        self.camera_table.setColumnCount(3)
        self.camera_table.setHorizontalHeaderLabels(["ID", "Tên", "Nguồn RTSP"])
        self.camera_table.setRowCount(len(self.cameras))
        for i, cam in enumerate(self.cameras):
            self.camera_table.setItem(i, 0, QTableWidgetItem(str(cam["id"])))
            self.camera_table.setItem(i, 1, QTableWidgetItem(cam["name"]))
            self.camera_table.setItem(i, 2, QTableWidgetItem(cam["source"]))
        layout.addWidget(QLabel("Danh sách camera:"))
        layout.addWidget(self.camera_table)

        # Nút thêm/sửa/xóa
        button_layout = QHBoxLayout()
        add_button = QPushButton("Thêm Camera")
        edit_button = QPushButton("Sửa Camera")
        delete_button = QPushButton("Xóa Camera")
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

        page.setLayout(layout)
        return page
    
    
    def delete_video(self):
        """Xóa video đã chọn"""
        selected_row = self.video_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một video để xóa!")
            return

        filename = self.video_table.item(selected_row, 0).text()
        cam_id = self.video_table.item(selected_row, 1).text()
        filepath = os.path.join("recordings", f"camera_{cam_id}", filename)

        # Xác nhận trước khi xóa
        confirm = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc muốn xóa video {filename}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            if os.path.exists(filepath):
                os.remove(filepath)
                self.video_table.removeRow(selected_row)
                QMessageBox.information(self, "Thành công", "Video đã được xóa.")
            else:
                QMessageBox.warning(self, "Lỗi", "Video không tồn tại!")

    def delete_all_videos(self):
        """Xóa tất cả video trong thư mục"""
        confirm = QMessageBox.question(
            self, "Xác nhận", "Bạn có chắc muốn xóa tất cả video?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            base_dir = "recordings"
            if os.path.exists(base_dir):
                for camera_folder in os.listdir(base_dir):
                    folder_path = os.path.join(base_dir, camera_folder)
                    for filename in os.listdir(folder_path):
                        if filename.endswith((".mp4", ".avi")):
                            filepath = os.path.join(folder_path, filename)
                            os.remove(filepath)
                self.load_recorded_videos()  # Cập nhật lại bảng video
                QMessageBox.information(self, "Thành công", "Tất cả video đã được xóa.")
            else:
                QMessageBox.warning(self, "Lỗi", "Không tìm thấy thư mục chứa video!")

    def build_review_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self.review_camera_filter = QComboBox()
        self.review_camera_filter.addItem("Tất cả camera")
        for cam in self.cameras:
            self.review_camera_filter.addItem(str(cam["id"]))
        self.review_start_date = QDateTimeEdit(QDateTime.currentDateTime().addDays(-7))
        self.review_end_date = QDateTimeEdit(QDateTime.currentDateTime())
        filter_button = QPushButton("Lọc")
        filter_button.clicked.connect(self.load_recorded_videos)
        filter_layout.addWidget(QLabel("Camera:"))
        filter_layout.addWidget(self.review_camera_filter)
        filter_layout.addWidget(QLabel("Từ:"))
        filter_layout.addWidget(self.review_start_date)
        filter_layout.addWidget(QLabel("Đến:"))
        filter_layout.addWidget(self.review_end_date)
        filter_layout.addWidget(filter_button)
        layout.addLayout(filter_layout)
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(4)
        self.video_table.setHorizontalHeaderLabels(["Tên file", "Camera", "Ngày tạo", "Dung lượng"])
        self.video_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.video_table.cellDoubleClicked.connect(self.play_selected_video)
        layout.addWidget(self.video_table)
        self.review_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.review_video_widget = QVideoWidget()
        self.review_player.setVideoOutput(self.review_video_widget)
        video_container = QHBoxLayout()
        video_container.addStretch()
        video_container.addWidget(self.review_video_widget)
        video_container.addStretch()
        layout.addLayout(video_container)
        delete_button = QPushButton("Xóa Video")
        delete_all_button = QPushButton("Xóa Tất Cả")
        delete_button.clicked.connect(self.delete_video)
        delete_all_button.clicked.connect(self.delete_all_videos)
        layout.addWidget(delete_button)
        layout.addWidget(delete_all_button)
        page.setLayout(layout)
        return page



    def load_recorded_videos(self):
        from datetime import datetime
        self.video_table.setRowCount(0)
        base_dir = "recordings"
        if not os.path.exists(base_dir):
            return
        selected_camera = self.review_camera_filter.currentText()
        start_dt = self.review_start_date.dateTime().toPyDateTime()
        end_dt = self.review_end_date.dateTime().toPyDateTime()
        row = 0
        for camera_folder in os.listdir(base_dir):
            cam_id = camera_folder.replace("camera_", "")
            if selected_camera != "Tất cả camera" and selected_camera != cam_id:
                continue
            folder_path = os.path.join(base_dir, camera_folder)
            for filename in os.listdir(folder_path):
                if not filename.endswith((".mp4", ".avi")):
                    continue
                filepath = os.path.join(folder_path, filename)
                file_stat = os.stat(filepath)
                created_time = datetime.fromtimestamp(file_stat.st_mtime)
                if not (start_dt <= created_time <= end_dt):
                    continue
                filesize = humanize.naturalsize(file_stat.st_size)
                created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
                self.video_table.insertRow(row)
                self.video_table.setItem(row, 0, QTableWidgetItem(filename))
                self.video_table.setItem(row, 1, QTableWidgetItem(cam_id))
                self.video_table.setItem(row, 2, QTableWidgetItem(created_str))
                self.video_table.setItem(row, 3, QTableWidgetItem(filesize))
                row += 1

    def play_selected_video(self, row, col):
        filename = self.video_table.item(row, 0).text()
        cam_id = self.video_table.item(row, 1).text()
        filepath = os.path.join("recordings", f"camera_{cam_id}", filename)
        if os.path.exists(filepath):
            self.review_video_widget.setFixedSize(640, 640)
            self.review_player.setMedia(QMediaContent(QUrl.fromLocalFile(filepath)))
            self.review_player.play()


    def update_page_label(self):
        per_page = 4 if self.grid_mode == "2x2" else 9
        total_pages = max(1, (len(self.cameras) + per_page - 1) // per_page)
        self.page_label.setText(f"Trang {self.current_page + 1} / {total_pages}")

    def display_cameras(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        per_page = 4 if self.grid_mode == "2x2" else 9
        start = self.current_page * per_page
        num_cols = 2 if self.grid_mode == "2x2" else 3
        for i in range(per_page):
            row = i // num_cols
            col = i % num_cols
            cam_index = start + i
            if cam_index < len(self.cameras):
                cam = self.cameras[cam_index]
                widget = CameraWidget(name=cam["name"], cam_id=cam["id"], camera_data=cam)
            else:
                widget = CameraPlaceholderWidget()
            self.grid_layout.addWidget(widget, row, col)
        self.update_page_label()
        self.update_connection_status()

        
    def change_layout(self, text):
        self.grid_mode = text
        self.current_page = 0
        
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Reinitialize empty slots with new layout
        self.initialize_empty_slots()
        
        # Redisplay cameras if any exist
        if self.cameras:
            self.display_cameras()
        
        self.update_page_label()

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
        if index == 2:  # Quản lý Cameras
            dialog = CameraManagerDialog(self.cameras, self)
            dialog.cameras_updated.connect(self.update_cameras)
            dialog.exec_()
        elif index == 3:  # Xem lại Video
            self.load_recorded_videos()
            self.pages.setCurrentIndex(2)
        elif index == 4:  # Quay Lại
            if self.main_window:
                self.main_window.show()
                self.back_to_main()
                self.hide()
        else:
            self.pages.setCurrentIndex(index)
    def update_cameras(self, cameras):
        self.cameras = cameras
        self.display_cameras()  # Cập nhật giao diện stream nếu cần

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())