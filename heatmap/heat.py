import cv2
import json
import time
from ultralytics import solutions
from ultralytics import YOLO

class ObjectCounter:
    """
    Class để đếm đối tượng qua nhiều đường line và hiển thị/lưu số liệu.
    """
    def __init__(self, model_path, classes_to_count, roi_list, save_interval=10):
        """
        Khởi tạo ObjectCounter.

        Args:
            model_path (str): Đường dẫn đến mô hình YOLO (ví dụ: 'yolo11n.pt').
            classes_to_count (list): Danh sách các lớp cần đếm (ví dụ: [0] cho người).
            roi_list (list): Danh sách ROI từ file JSON, mỗi ROI có 'name', 'start', 'end'.
            save_interval (int): Khoảng thời gian (giây) giữa các lần lưu số liệu (mặc định: 10 giây).
        """
        self.model_path = model_path
        self.classes_to_count = classes_to_count
        self.save_interval = save_interval
        self.last_save_time = time.time()

        # Khởi tạo danh sách các bộ đếm
        self.counters = []
        self.line_names = []
        for roi in roi_list:
            if "start" in roi and "end" in roi:
                # Chuyển đổi start và end thành định dạng [(x1, y1), (x2, y2)]
                line_points = [
                    (int(roi['start'][0]), int(roi['start'][1])),
                    (int(roi['end'][0]), int(roi['end'][1]))
                ]
                counter = solutions.ObjectCounter(
                    view=True,
                    region=line_points,
                    model=model_path,
                    classes=classes_to_count
                )
                self.counters.append(counter)
                self.line_names.append(roi.get('name', f"Line {len(self.counters)}"))
                print(f"Đã thêm bộ đếm cho {roi.get('name', 'Line')} với điểm: {line_points}")
            else:
                print(f"Bỏ qua ROI không hợp lệ: {roi.get('name', 'Không có tên')}")

        if not self.counters:
            raise ValueError("Không có đường line hợp lệ để đếm.")

    def count(self, frame):
        """
        Đếm đối tượng trên frame và hiển thị số liệu lên frame.

        Args:
            frame (np.ndarray): Frame video đầu vào.

        Returns:
            tuple: (frame đã vẽ, dictionary chứa số liệu đếm).
        """
        im0 = frame.copy()
        counts = {}

        # Áp dụng từng bộ đếm và hiển thị số liệu
        for idx, counter in enumerate(self.counters):
            results = counter(im0)
            im0 = results.plot_im  # Frame đã vẽ line và các đối tượng

            # Lấy số liệu in/out từ counter
            in_count = counter.in_count
            out_count = counter.out_count
            line_name = self.line_names[idx]
            counts[line_name] = {"in": in_count, "out": out_count}

            # Hiển thị số liệu lên frame gần điểm đầu của line
            start_point = counter.region[0]  # Điểm đầu của line
            text = f"{line_name}: In {in_count} / Out {out_count}"
            cv2.putText(im0, text, (start_point[0], start_point[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return im0, counts

    def save_counts(self, filename):
        """
        Lưu số liệu đếm vào file JSON nếu đã đến thời điểm lưu.

        Args:
            filename (str): Đường dẫn đến file JSON để lưu.
        """
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            counts = {}
            for idx, counter in enumerate(self.counters):
                line_name = self.line_names[idx]
                counts[line_name] = {"in": counter.in_count, "out": counter.out_count}

            data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "counts": counts
            }

            # Ghi thêm vào file JSON
            try:
                with open(filename, 'r') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            existing_data.append(data)
            with open(filename, 'w') as f:
                json.dump(existing_data, f, indent=4)

            self.last_save_time = current_time
            print(f"Đã lưu số liệu vào {filename} tại {data['timestamp']}")

    def get_total_counts(self):
        """
        Tính tổng số liệu từ tất cả các line.

        Returns:
            dict: Tổng số liệu {"total": int, "in": int, "out": int}.
        """
        total_in = sum(counter.in_count for counter in self.counters)
        total_out = sum(counter.out_count for counter in self.counters)
        return {"total": total_in + total_out, "in": total_in, "out": total_out}