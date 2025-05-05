import cv2
import time
import json
import os
import numpy as np
import supervision as sv
from ultralytics import YOLO
import torch

class ObjectCounter:
    """
    ObjectCounter using YOLOv8x and supervision ByteTrack for multi-ROI counting per camera.
    """

    def __init__(self, model_path, classes_to_count, roi_list, save_interval=10, threshold=0.25, device=None):
        """
        Initialize ObjectCounter.

        Args:
            model_path (str): Path to YOLO model.
            classes_to_count (list): List of class IDs to count.
            roi_list (list): List of ROIs, each with 'name', 'start', 'end' points.
            save_interval (int): Seconds between saving counts to JSON.
            threshold (float): Confidence threshold for detections.
            device (str or torch.device): Device to run model on.
        """
        self.model_path = model_path
        self.classes_to_count = classes_to_count
        self.roi_list = roi_list
        self.save_interval = save_interval
        self.threshold = threshold
        self.last_save_time = time.time()
        self.device = device if device else ("cuda:0" if torch.cuda.is_available() else "cpu")

        self.model = YOLO(self.model_path)
        self.model.to(self.device)

        self.byte_tracker = sv.ByteTrack()
        self.corner_annotator = sv.BoxCornerAnnotator()
        self.label_annotator = sv.LabelAnnotator(text_position=sv.Position.CENTER)
        self.trace_annotator = sv.TraceAnnotator(thickness=4)

        # Create LineZones for each ROI
        self.line_zones = []
        self.line_zone_annotators = []
        self.line_names = []
        for roi in self.roi_list:
            if "start" in roi and "end" in roi:
                start_point = sv.Point(int(roi['start'][0]), int(roi['start'][1]))
                end_point = sv.Point(int(roi['end'][0]), int(roi['end'][1]))
                line_zone = sv.LineZone(start=start_point, end=end_point)
                self.line_zones.append(line_zone)
                self.line_zone_annotators.append(sv.LineZoneAnnotator(thickness=4, text_thickness=4, text_scale=1.5))
                self.line_names.append(roi.get('name', f"Line {len(self.line_zones)}"))
                
            else:
                print(f"Invalid ROI skipped: {roi.get('name', 'No name')}")

        if not self.line_zones:
            raise ValueError("No valid ROIs provided for counting.")

    def count(self, frame):
        """
        Count objects on the frame for all ROIs.

        Args:
            frame (np.ndarray): Input video frame.

        Returns:
            np.ndarray: Annotated frame.
            dict: Counts per ROI line.
        """
        im0 = frame.copy()
        counts = {}

        # Run YOLO model on frame
        results = self.model(im0, verbose=False, device=self.device)[0]

        # Filter detections by class and confidence
        detections = sv.Detections.from_ultralytics(results)
        detections = detections[np.isin(detections.class_id, self.classes_to_count) & (detections.confidence > self.threshold)]

        # Update tracker
        tracked_detections = self.byte_tracker.update_with_detections(detections)

        # Annotate bounding boxes and traces
        im0 = self.trace_annotator.annotate(scene=im0, detections=tracked_detections)
        im0 = self.corner_annotator.annotate(scene=im0, detections=tracked_detections)

        labels = []
        if tracked_detections is not None and len(tracked_detections) > 0:
            for cls_id, conf, tid in zip(tracked_detections.class_id, tracked_detections.confidence, tracked_detections.tracker_id):
                class_name = self.model.model.names.get(int(cls_id), str(cls_id)) if hasattr(self, 'model') else str(cls_id)
                labels.append(f"#{tid} {class_name} {conf:.2f}")
        im0 = self.label_annotator.annotate(scene=im0, detections=tracked_detections, labels=labels)

        # Count objects crossing each line zone
        for idx, line_zone in enumerate(self.line_zones):
            line_zone.trigger(tracked_detections)
            im0 = self.line_zone_annotators[idx].annotate(im0, line_counter=line_zone)
            counts[self.line_names[idx]] = {"in": line_zone.in_count, "out": line_zone.out_count}

        return im0, counts

    def save_counts(self, filename):
        """
        Save counts to JSON file if save interval elapsed.

        Args:
            filename (str): Path to JSON file.
        """
        current_time = time.time()
        if current_time - self.last_save_time >= self.save_interval:
            data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "counts": {}
            }
            for idx, line_zone in enumerate(self.line_zones):
                data["counts"][self.line_names[idx]] = {"in": line_zone.in_count, "out": line_zone.out_count}

            # Append to existing JSON or create new
            try:
                with open(filename, 'r') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            existing_data.append(data)
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(existing_data, f, indent=4)

            self.last_save_time = current_time
            print(f"Saved counts to {filename} at {data['timestamp']}")

    def get_total_counts(self):
        """
        Get total counts across all lines.

        Returns:
            dict: {"total": int, "in": int, "out": int}
        """
        total_in = sum(line_zone.in_count for line_zone in self.line_zones)
        total_out = sum(line_zone.out_count for line_zone in self.line_zones)
        return {"total": total_in + total_out, "in": total_in, "out": total_out}
