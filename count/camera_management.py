# camera_management.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal

class CameraManagerDialog(QDialog):
    cameras_updated = pyqtSignal(list)  # Signal để gửi danh sách camera

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quản lý Camera")
        self.resize(400, 300)
        self.camera_list = []

        self.layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Thêm Camera")
        edit_btn = QPushButton("✏️ Chỉnh sửa")
        delete_btn = QPushButton("❌ Xóa")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        self.layout.addLayout(btn_layout)

        confirm_btn = QPushButton("✅ Xác nhận")
        self.layout.addWidget(confirm_btn)

        self.setLayout(self.layout)

        add_btn.clicked.connect(self.add_camera)
        edit_btn.clicked.connect(self.edit_camera)
        delete_btn.clicked.connect(self.delete_camera)
        confirm_btn.clicked.connect(self.confirm)

    def add_camera(self):
        dialog = CameraInputDialog()
        if dialog.exec_():
            name, path = dialog.get_data()
            self.camera_list.append((len(self.camera_list), path))
            self.list_widget.addItem(f"{name}: {path}")

    def edit_camera(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        old_name, old_path = self.list_widget.item(row).text().split(": ")
        dialog = CameraInputDialog(old_name, old_path)
        if dialog.exec_():
            name, path = dialog.get_data()
            self.camera_list[row] = (row, path)
            self.list_widget.item(row).setText(f"{name}: {path}")

    def delete_camera(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.camera_list.pop(row)
            self.list_widget.takeItem(row)

    def confirm(self):
        self.cameras_updated.emit(self.camera_list)
        self.accept()

class CameraInputDialog(QDialog):
    def __init__(self, name="", path=""):
        super().__init__()
        self.setWindowTitle("Thông tin Camera")
        self.resize(300, 100)

        self.name_input = QLineEdit(name)
        self.path_input = QLineEdit(path)
        browse_btn = QPushButton("Tải video")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tên camera:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Đường dẫn video / RTSP:"))
        layout.addWidget(self.path_input)
        layout.addWidget(browse_btn)

        confirm_btn = QPushButton("OK")
        layout.addWidget(confirm_btn)

        self.setLayout(layout)

        browse_btn.clicked.connect(self.browse_file)
        confirm_btn.clicked.connect(self.accept)

    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Chọn video")
        if file:
            self.path_input.setText(file)

    def get_data(self):
        return self.name_input.text(), self.path_input.text()
