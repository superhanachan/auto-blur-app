import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from ultralytics import YOLO
import supervision as sv

def apply_mosaic(image, box, level, padding=0):
    x1, y1, x2, y2 = [int(v) for v in box]
    
    w = x2 - x1
    h = y2 - y1
    x1 = max(0, x1 - int(w * padding))
    y1 = max(0, y1 - int(h * padding))
    x2 = min(image.shape[1], x2 + int(w * padding))
    y2 = min(image.shape[0], y2 + int(h * padding))
    
    if x2 <= x1 or y2 <= y1:
        return image
        
    roi = image[y1:y2, x1:x2]
    
    if level <= 0:
        return image
        
    # level 1-100, where 100 is max pixelation
    factor = max(1, 101 - level) 
    
    # Resize down
    small = cv2.resize(roi, (max(1, roi.shape[1] // factor), max(1, roi.shape[0] // factor)), interpolation=cv2.INTER_LINEAR)
    # Resize up
    mosaic_roi = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
    
    image[y1:y2, x1:x2] = mosaic_roi
    return image


class VideoExporter(QThread):
    progress_signal = pyqtSignal(int, int, int) # current, total, percentage
    finished_signal = pyqtSignal(bool, str) # success, message
    
    def __init__(self, video_path, output_path, config):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.config = config
        self.is_running = False
        self._face_model = None
        self._plate_model = None
        self.byte_tracker = None
        
    def load_models(self):
        try:
            if self._face_model is None:
                self._face_model = YOLO("models/yolov8n-face.pt")
        except:
            self._face_model = YOLO("yolov8n.pt")
            
        try:
            if self._plate_model is None:
                self._plate_model = YOLO("models/yolov8n-plate.pt")
        except:
            self._plate_model = YOLO("yolov8n.pt")

    def process_frame(self, frame, tracking=False):
        self.load_models()
        detections_list = []
        
        if self.config.get('detect_face', True):
            res = self._face_model(frame, conf=self.config.get('conf', 0.35), verbose=False)[0]
            det = sv.Detections.from_ultralytics(res)
            # If fallback model
            if "yolov8n.pt" in self._face_model.ckpt_path:
                 det = det[det.class_id == 0]
            detections_list.append(det)
            
        if self.config.get('detect_plate', True):
            res = self._plate_model(frame, conf=self.config.get('conf', 0.35), verbose=False)[0]
            det = sv.Detections.from_ultralytics(res)
            # If fallback model (car/truck/bus)
            if "yolov8n.pt" in self._plate_model.ckpt_path:
                 mask = np.isin(det.class_id, [2, 5, 7])
                 det = det[mask]
            detections_list.append(det)
            
        if not detections_list:
             return frame
             
        bboxes = np.vstack([d.xyxy for d in detections_list if len(d.xyxy) > 0] or [np.empty((0,4))])
        confidences = np.concatenate([d.confidence for d in detections_list if len(d.confidence) > 0] or [np.array([])])
        class_ids = np.concatenate([d.class_id for d in detections_list if len(d.class_id) > 0] or [np.array([])])
        
        if len(bboxes) > 0:
            merged = sv.Detections(xyxy=bboxes, confidence=confidences, class_id=class_ids)
        else:
            merged = sv.Detections.empty()

        if tracking and len(merged) > 0:
             if self.byte_tracker is None:
                  self.byte_tracker = sv.ByteTrack()
             merged = self.byte_tracker.update_with_detections(merged)
             
        processed_frame = frame.copy()
        for box in merged.xyxy:
             processed_frame = apply_mosaic(processed_frame, box, self.config.get('mosaic', 80), self.config.get('padding', 0.1))
             
        return processed_frame

    def run(self):
        try:
            self.is_running = True
            
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.finished_signal.emit(False, "Could not open video.")
                return
                
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            import imageio
            out = imageio.get_writer(self.output_path, fps=fps, codec='libx264', quality=7, macro_block_size=None)
            
            self.byte_tracker = sv.ByteTrack() 
            
            current_frame = 0
            while self.is_running and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                processed = self.process_frame(frame, tracking=True)
                processed_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
                out.append_data(processed_rgb)
                
                current_frame += 1
                if current_frame % 5 == 0 or current_frame == total_frames:
                    pct = int(current_frame / total_frames * 100)
                    self.progress_signal.emit(current_frame, total_frames, pct)
                    
            cap.release()
            out.close()
            
            if self.is_running:
                self.finished_signal.emit(True, "Export completed successfully.")
            else:
                self.finished_signal.emit(False, "Export cancelled.")
        except Exception as e:
            import traceback
            self.finished_signal.emit(False, f"Export Error:\n{traceback.format_exc()}")
            
    def stop(self):
        self.is_running = False
        self.wait()
