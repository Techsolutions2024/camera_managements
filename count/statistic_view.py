from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QComboBox, QPushButton, QFrame
from PyQt5.QtCore import Qt
from count.data_manager import DataManager

class StatisticsView(QWidget):
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.initUI()

    def initUI(self):
        # Tạo layout chính
        layout = QGridLayout()
        self.setLayout(layout)

        # Cột trái
        left_column = QFrame()
        left_layout = QGridLayout()
        left_column.setLayout(left_layout)
        

        # Thống kê thời gian thực
        realtime_frame = QFrame()
        realtime_layout = QGridLayout()
        realtime_frame.setLayout(realtime_layout)
        realtime_layout.addWidget(QLabel("Thống kê thời gian thực"), 0, 0, 1, 2, alignment=Qt.AlignCenter)
        realtime_layout.addWidget(QLabel("[Biểu đồ tròn % IN]"), 1, 0)
        realtime_layout.addWidget(QLabel("[Biểu đồ tròn % OUT]"), 1, 1)
        self.realtime_label = QLabel("Tổng IN: 0   Tổng OUT: 0")  # Thêm label để cập nhật
        realtime_layout.addWidget(self.realtime_label, 2, 0, 1, 2, alignment=Qt.AlignCenter)
        self.camera_combo = QComboBox()  # ComboBox chọn camera
        realtime_layout.addWidget(self.camera_combo, 3, 0, 1, 2)
        left_layout.addWidget(realtime_frame, 0, 0)
        

        # Lượng người theo thời gian
        time_series_frame = QFrame()
        time_series_layout = QGridLayout()
        time_series_frame.setLayout(time_series_layout)
        time_series_layout.addWidget(QLabel("Lượng người theo thời gian"), 0, 0, 1, 2, alignment=Qt.AlignCenter)
        time_series_layout.addWidget(QLabel("[Biểu đồ cột IN/OUT]"), 1, 0, 1, 2)
        time_series_layout.addWidget(QComboBox(), 2, 0)  # ComboBox chọn khoảng thời gian
        time_series_layout.addWidget(QPushButton("Làm mới"), 2, 1)
        left_layout.addWidget(time_series_frame, 1, 0)
        

        # Phần trống
        left_layout.addWidget(QFrame(), 2, 0)

        layout.addWidget(left_column, 0, 0)

        # Cột phải
        right_column = QFrame()
        right_layout = QGridLayout()
        right_column.setLayout(right_layout)

        # So sánh theo tháng
        monthly_comparison_frame = QFrame()
        monthly_comparison_layout = QGridLayout()
        monthly_comparison_frame.setLayout(monthly_comparison_layout)
        monthly_comparison_layout.addWidget(QLabel("So sánh theo tháng"), 0, 0, 1, 2, alignment=Qt.AlignCenter)
        monthly_comparison_layout.addWidget(QLabel("[Biểu đồ cột so sánh IN/OUT]"), 1, 0, 1, 2)
        monthly_comparison_layout.addWidget(QComboBox(), 2, 0)  # ComboBox chọn tháng
        monthly_comparison_layout.addWidget(QPushButton("Xuất PNG"), 2, 1)
        right_layout.addWidget(monthly_comparison_frame, 0, 0)

        # Tổng lượng người
        total_people_frame = QFrame()
        total_people_layout = QGridLayout()
        total_people_frame.setLayout(total_people_layout)
        total_people_layout.addWidget(QLabel("Tổng lượng người"), 0, 0, 1, 2, alignment=Qt.AlignCenter)
        total_people_layout.addWidget(QLabel("Tổng IN: X   Tổng OUT: Y"), 1, 0, 1, 2, alignment=Qt.AlignCenter)
        total_people_layout.addWidget(QComboBox(), 2, 0)  # ComboBox chọn khoảng thời gian
        total_people_layout.addWidget(QPushButton("Cập nhật"), 2, 1)
        right_layout.addWidget(total_people_frame, 1, 0)

        layout.addWidget(right_column, 0, 1)

        # Thiết lập tỷ lệ kéo giãn
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        left_layout.setRowStretch(0, 1)
        left_layout.setRowStretch(1, 1)
        left_layout.setRowStretch(2, 2)
        right_layout.setRowStretch(0, 1)
        right_layout.setRowStretch(1, 1)
        
    def update_realtime_stats(self, cam_id):
        cursor = self.data_manager.conn.cursor()
        cursor.execute('''
            SELECT in_count, out_count, total_count FROM stats
            WHERE camera_id = ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (cam_id,))
        stats = cursor.fetchone()
        if stats:
            in_count, out_count, total_count = stats
            self.realtime_label.setText(f"Tổng IN: {in_count}   Tổng OUT: {out_count}")