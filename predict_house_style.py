
from ultralytics import YOLO
import cv2
import numpy as np

MODEL_PATH = "weights/best.pt"  # update to correct local or remote path
model = YOLO(MODEL_PATH)

def predict_style(image_path):
    results = model(image_path)
    preds = []

    for box, cls, conf in zip(results[0].boxes.xyxy, results[0].boxes.cls, results[0].boxes.conf):
        label = model.names[int(cls)]
        preds.append({
            "label": label,
            "confidence": float(conf),
            "bbox": box.cpu().numpy()
        })

    return preds, results[0]
    