from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QInputDialog, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QFileDialog
import os
import json

class CameraManagerDialog(QDialog):
    # Signal để gửi danh sách camera đã cập nhật về main.py
    cameras_updated = pyqtSignal(list)

    def __init__(self, cameras, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý Camera")
        self.setMinimumSize(600, 400)
        self.cameras = cameras  # Danh sách camera từ main.py

        # Layout chính
        layout = QVBoxLayout()

        # Bảng hiển thị danh sách camera
        self.camera_table = QTableWidget()
        self.camera_table.setColumnCount(3)
        self.camera_table.setHorizontalHeaderLabels(["ID", "Tên", "Nguồn RTSP/Video"])
        self.update_camera_table()  # Cập nhật bảng ban đầu
        layout.addWidget(self.camera_table)

        # Các nút điều khiển
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Thêm Camera")
        self.edit_button = QPushButton("Chỉnh sửa Camera")
        self.delete_button = QPushButton("Xóa Camera")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Kết nối sự kiện cho các nút
        self.add_button.clicked.connect(self.add_camera)
        self.edit_button.clicked.connect(self.edit_camera)
        self.delete_button.clicked.connect(self.delete_camera)

    def update_camera_table(self):
        """Cập nhật bảng với danh sách camera hiện tại"""
        self.camera_table.setRowCount(len(self.cameras))
        for i, cam in enumerate(self.cameras):
            self.camera_table.setItem(i, 0, QTableWidgetItem(str(cam["id"])))
            self.camera_table.setItem(i, 1, QTableWidgetItem(cam["name"]))
            self.camera_table.setItem(i, 2, QTableWidgetItem(cam["source"]))


            
    def save_camera_list(self):
        """Lưu danh sách camera vào file JSON"""
        try:
            with open('modulecam/camera_list.json', 'w') as f:
                json.dump(self.cameras, f, indent=4)  # Lưu danh sách camera vào tệp JSON
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Error saving camera list: {str(e)}")

    
    def add_camera(self):
        """Thêm camera mới"""
        # Chọn loại nguồn
        source_type, ok = QInputDialog.getItem(
            self, "Thêm Camera", "Chọn loại nguồn:", ["Video local", "RTSP"], 0, False
        )
        if not ok:
            return

        # Nhập ID camera
        id, ok = QInputDialog.getInt(self, "Thêm Camera", "Nhập ID camera:", min=1)
        if not ok:
            return

        # Nhập tên camera
        name, ok = QInputDialog.getText(self, "Thêm Camera", "Nhập tên camera:")
        if not ok:
            return

        # Nhập nguồn dựa trên loại
        if source_type == "Video local":
            # Mở hộp thoại chọn file video
            source, _ = QFileDialog.getOpenFileName(
                self, "Chọn video local", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
            )
            if not source:  # Người dùng nhấn Cancel
                return
        else:  # RTSP
            source, ok = QInputDialog.getText(self, "Thêm Camera", "Nhập URL RTSP:")
            if not ok:
                return
            # Kiểm tra định dạng URL cơ bản
            if not source.startswith("rtsp://"):
                QMessageBox.warning(self, "Lỗi", "URL RTSP không hợp lệ!")
                return

        # Kiểm tra ID trùng lặp
        if any(cam["id"] == id for cam in self.cameras):
            QMessageBox.warning(self, "Lỗi", "ID camera đã tồn tại!")
            return

        # Lưu thông tin camera
        new_camera = {
            "id": id,
            "name": name,
            "source": source,
            "type": source_type.lower().replace(" ", "_")  # "video_local" hoặc "rtsp"
        }
        self.cameras.append(new_camera)
        self.update_camera_table()  # Cập nhật giao diện bảng camera
        self.save_camera_list()  # Lưu camera mới vào file
        self.cameras_updated.emit(self.cameras)  # Gửi signal về chương trình chính


    def edit_camera(self):
        """Chỉnh sửa camera đã chọn"""
        selected_row = self.camera_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một camera để chỉnh sửa!")
            return

        cam = self.cameras[selected_row]

        # Nhập thông tin mới cho camera
        id, ok = QInputDialog.getInt(self, "Chỉnh sửa Camera", "Nhập ID camera:", value=cam["id"], min=1)
        if not ok:
            return
        name, ok = QInputDialog.getText(self, "Chỉnh sửa Camera", "Nhập tên camera:", text=cam["name"])
        if not ok:
            return
        source, ok = QInputDialog.getText(self, "Chỉnh sửa Camera", "Nhập nguồn RTSP/Video:", text=cam["source"])
        if not ok:
            return

        # Kiểm tra ID trùng lặp (nếu thay đổi ID)
        if id != cam["id"] and any(c["id"] == id for c in self.cameras):
            QMessageBox.warning(self, "Lỗi", "ID camera đã tồn tại!")
            return

        # Cập nhật thông tin camera
        cam["id"] = id
        cam["name"] = name
        cam["source"] = source
        self.update_camera_table()
        self.save_camera_list()  # Lưu camera đã chỉnh sửa vào file
        self.cameras_updated.emit(self.cameras)  # Gửi signal về main.py

    def delete_camera(self):
        """Xóa camera đã chọn"""
        selected_row = self.camera_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một camera để xóa!")
            return

        # Xác nhận trước khi xóa
        confirm = QMessageBox.question(
            self, "Xác nhận", "Bạn có chắc muốn xóa camera này?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.cameras[selected_row]
            self.update_camera_table()
            self.save_camera_list()  # Lưu lại danh sách camera sau khi xóa
            self.cameras_updated.emit(self.cameras)  # Gửi signal về main.py
