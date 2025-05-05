import sqlite3
import os
from datetime import datetime

class DataManager:
    def __init__(self, db_path="stats_data/stats.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER,
                timestamp TEXT,
                in_count INTEGER,
                out_count INTEGER,
                total_count INTEGER
            )
        ''')
        # Tạo chỉ mục cho camera_id và timestamp để truy vấn nhanh hơn
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_camera_id ON stats(camera_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON stats(timestamp)')
        self.conn.commit()

    def save_stats(self, cam_id, in_count, out_count, total_count):
        cursor = self.conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO stats (camera_id, timestamp, in_count, out_count, total_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (cam_id, timestamp, in_count, out_count, total_count))
        self.conn.commit()

    def close(self):
        self.conn.close()
