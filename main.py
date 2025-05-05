from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from modulecam.camera import MainWindow as CameraMainWindow
from count.count_moudle import MainWindow as CountingMainWindow
from heatmap.heat_module import MainWindow as HeatMapMainWindow
import json
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giao Diện Quản Lý Camera")
        self.resize(1400, 900)  # Giảm kích thước giao diện xuống

        # Đặt màu nền và kiểu giao diện
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
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QWidget {
                background-color: #ffffff;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
                text-align: center;
                min-width: 180px;
                max-width: 200px;  # Giới hạn kích thước widget để giữ giao diện cân đối
                margin-bottom: 30px;
            }
            QGridLayout {
                spacing: 30px;
                margin: 20px;
            }
            QVBoxLayout {
                align-items: center;
                justify-content: center;
                spacing: 10px;
            }
        """)

        # Layout chính của giao diện
        main_layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Thiết lập Grid Layout cho các chức năng
        grid_layout = QGridLayout()
        grid_layout.setSpacing(30)

        # Các widget chức năng
        self.create_function_widget(grid_layout, "Quản Lý Camera", "🎥", "Quản lý và điều chỉnh các camera", self.manage_camera, 0, 0)
        self.create_function_widget(grid_layout, "Đếm Người", "👤", "Đếm số người trong video", self.launch_counting_interface, 0, 1)
        self.create_function_widget(grid_layout, "Heatmap", "🌡️", "Hiển thị heatmap từ video", self.launch_heatmap_interface, 0, 2)
        self.create_function_widget(grid_layout, "Cài Đặt", "⚙️", "Chỉnh sửa cài đặt hệ thống", self.settings, 1, 0)
        self.create_function_widget(grid_layout, "Trợ Giúp", "❓", "Cung cấp thông tin trợ giúp", self.help, 1, 1)
        self.create_function_widget(grid_layout, "Hướng Dẫn Sử Dụng", "📚", "Hướng dẫn sử dụng chi tiết", self.user_guide, 1, 2)
        self.create_function_widget(grid_layout, "Đăng Xuất", "🚪", "Đăng xuất khỏi hệ thống", self.logout, 2, 0)

        # Đặt Grid Layout vào Layout chính
        main_layout.addLayout(grid_layout)

    def create_function_widget(self, layout, text, icon, description, function, row, col):
        """Tạo một widget chức năng với icon emoji, tiêu đề và mô tả ngắn, sắp xếp vào vị trí trong grid"""
        widget = QWidget()
        widget_layout = QVBoxLayout()

        # Thêm biểu tượng emoji cho widget
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 60px; margin-bottom: 5px;")  # Điều chỉnh khoảng cách giữa emoji và text

        # Thêm tiêu đề cho widget
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")

        # Thêm mô tả cho widget
        description_label = QLabel(description)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("font-size: 12px; color: #666; margin-top: 5px;")

        # Thêm nút bấm để kích hoạt chức năng
  
        button = QPushButton("Chọn")
        if text == "Đếm Người":
            button.clicked.connect(self.launch_counting_interface)  # Connect to new method
            
        elif text == "Heatmap":
            button.clicked.connect(self.launch_heatmap_interface)
        else:
            button.clicked.connect(function)


        # Set layout for the widget
        widget_layout.addWidget(icon_label)
        widget_layout.addWidget(label)
        widget_layout.addWidget(description_label)
        widget_layout.addWidget(button)
        widget.setLayout(widget_layout)

        # Add widget to grid layout at position (row, col)
        layout.addWidget(widget, row, col)
        
    def manage_camera(self):
        """Launch the full camera management interface"""
        self.camera_window = CameraMainWindow(main_window=self)  # Pass main window reference
        self.camera_window.show()  # Show the camera management window
        self.hide()
    def load_camera_list(self):
        """Load camera list from JSON file"""
        try:
            if os.path.exists('modulecam/camera_list.json'):
                with open('modulecam/camera_list.json', 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error loading camera list: {str(e)}")
            return []

    def save_camera_list(self, cameras):
        """Save updated camera list to JSON file"""
        try:
            with open('modulecam/camera_list.json', 'w') as f:
                json.dump(cameras, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error saving camera list: {str(e)}")

    def launch_counting_interface(self):
        """Launch the full counting interface"""
        self.counting_window = CountingMainWindow(main_window=self)  # Pass main window reference
        self.counting_window.show()  # Show the counting window
        self.hide()  # Hide the main window

    def launch_heatmap_interface(self):
        """Launch the full heatmap interface"""
        self.heatmap_window = HeatMapMainWindow(main_window=self)  # Pass main window reference
        self.heatmap_window.show()  # Show the heatmap window
        self.hide()
    def settings(self):
        """Chức năng cài đặt"""
        print("Cài Đặt")

    def help(self):
        """Chức năng trợ giúp"""
        print("Trợ Giúp")

    def user_guide(self):
        """Chức năng hướng dẫn sử dụng"""
        print("Hướng Dẫn Sử Dụng")

    def logout(self):
        """Chức năng đăng xuất"""
        print("Đăng Xuất")

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()