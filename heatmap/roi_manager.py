# roi_manager.py
import json
import os

def save_roi(camera_name, roi_lines, folder="roi_data"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{camera_name}.json")
    with open(path, "w") as f:
        json.dump({"lines": roi_lines}, f, indent=4)

def load_roi(camera_name, folder="roi_data"):
    path = os.path.join(folder, f"{camera_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            return data.get("lines", [])
    return []
