import cv2
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QSlider, QCheckBox, QProgressBar, QMessageBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from processor import VideoExporter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Blur & Track")
        self.resize(1000, 700)
        
        self.video_path = ""
        self.cap = None
        self.total_frames = 0
        self.current_frame_idx = 0
        self.is_playing = False
        
        # Processor for preview
        self.preview_processor = VideoExporter("", "", {})
        self.exporter = None
        
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Left Panel (Video Player)
        left_layout = QVBoxLayout()
        
        self.video_label = QLabel("ドラッグ＆ドロップまたはファイルを選択")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000; color: #fff;")
        self.video_label.setMinimumSize(640, 360)
        left_layout.addWidget(self.video_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.btn_play = QPushButton("再生")
        self.btn_play.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.btn_play)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self.seek)
        controls_layout.addWidget(self.slider)
        
        left_layout.addLayout(controls_layout)
        layout.addLayout(left_layout, stretch=2)
        
        # Right Panel (Settings)
        right_layout = QVBoxLayout()
        
        self.btn_open = QPushButton("動画を開く")
        self.btn_open.clicked.connect(self.open_file)
        right_layout.addWidget(self.btn_open)
        
        settings_group = QGroupBox("検出設定")
        settings_form = QFormLayout()
        
        self.chk_face = QCheckBox("人物の顔")
        self.chk_face.setChecked(True)
        self.chk_plate = QCheckBox("車両ナンバープレート")
        self.chk_plate.setChecked(True)
        
        self.chk_preview_blur = QCheckBox("プレビューにモザイク適用")
        self.chk_preview_blur.setChecked(True)
        
        settings_form.addRow("対象:", self.chk_face)
        settings_form.addRow("", self.chk_plate)
        settings_form.addRow("表示:", self.chk_preview_blur)
        
        self.sld_conf = QSlider(Qt.Orientation.Horizontal)
        self.sld_conf.setRange(10, 100)
        self.sld_conf.setValue(35)
        settings_form.addRow("信頼度閾値:", self.sld_conf)
        
        self.sld_mosaic = QSlider(Qt.Orientation.Horizontal)
        self.sld_mosaic.setRange(1, 100)
        self.sld_mosaic.setValue(80)
        settings_form.addRow("モザイク強度:", self.sld_mosaic)
        
        self.sld_padding = QSlider(Qt.Orientation.Horizontal)
        self.sld_padding.setRange(0, 50) # 0 to 0.5 ratio
        self.sld_padding.setValue(10)
        settings_form.addRow("余白拡大:", self.sld_padding)
        
        settings_group.setLayout(settings_form)
        right_layout.addWidget(settings_group)
        
        export_group = QGroupBox("エクスポート")
        export_layout = QVBoxLayout()
        
        self.btn_export = QPushButton("書き出し開始")
        self.btn_export.clicked.connect(self.start_export)
        export_layout.addWidget(self.btn_export)
        
        self.btn_cancel = QPushButton("キャンセル")
        self.btn_cancel.clicked.connect(self.cancel_export)
        self.btn_cancel.setEnabled(False)
        export_layout.addWidget(self.btn_cancel)
        
        self.progress = QProgressBar()
        export_layout.addWidget(self.progress)
        
        export_group.setLayout(export_layout)
        right_layout.addWidget(export_group)
        
        right_layout.addStretch()
        layout.addLayout(right_layout, stretch=1)
        
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_video(files[0])
            
    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "動画を開く", "", "Video Files (*.mp4 *.mov *.avi)")
        if file:
            self.load_video(file)
            
    def load_video(self, path):
        try:
            self.video_path = path
            if self.cap:
                self.cap.release()
            self.cap = cv2.VideoCapture(path)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.slider.setRange(0, self.total_frames - 1)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.timer.setInterval(int(1000 / (fps if fps > 0 else 30)))
            
            self.current_frame_idx = 0
            self.slider.setValue(0)
            self.show_frame()
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Crash Error", f"load_video error:\n{traceback.format_exc()}")
            
    def get_config(self):
        return {
            'detect_face': self.chk_face.isChecked(),
            'detect_plate': self.chk_plate.isChecked(),
            'conf': self.sld_conf.value() / 100.0,
            'mosaic': self.sld_mosaic.value(),
            'padding': self.sld_padding.value() / 100.0
        }

    def show_frame(self):
        try:
            if not self.cap or not self.cap.isOpened():
                return
                
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_idx)
            ret, frame = self.cap.read()
            if ret:
                if self.chk_preview_blur.isChecked():
                    self.preview_processor.config = self.get_config()
                    frame = self.preview_processor.process_frame(frame, tracking=False)
                    
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Crash Error", f"show_frame error:\n{traceback.format_exc()}")
            
    def toggle_play(self):
        if self.is_playing:
            self.timer.stop()
            self.btn_play.setText("再生")
        else:
            if self.cap:
                self.timer.start()
                self.btn_play.setText("一時停止")
        self.is_playing = not self.is_playing
        
    def next_frame(self):
        if self.current_frame_idx < self.total_frames - 1:
            self.current_frame_idx += 1
            self.slider.setValue(self.current_frame_idx)
            self.show_frame()
        else:
            self.toggle_play()
            
    def seek(self, pos):
        self.current_frame_idx = pos
        self.show_frame()
        
    def start_export(self):
        if not self.video_path:
            QMessageBox.warning(self, "エラー", "動画が選択されていません。")
            return
            
        out_path, _ = QFileDialog.getSaveFileName(self, "保存先を選択", "output.mp4", "MP4 Files (*.mp4)")
        if not out_path:
            return
            
        self.btn_export.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setValue(0)
        
        # Stop playback if running
        if self.is_playing:
            self.toggle_play()
            
        self.exporter = VideoExporter(self.video_path, out_path, self.get_config())
        self.exporter.progress_signal.connect(self.update_progress)
        self.exporter.finished_signal.connect(self.export_finished)
        self.exporter.start()
        
    def cancel_export(self):
        if self.exporter:
            self.exporter.stop()
            
    def update_progress(self, current, total, pct):
        self.progress.setValue(pct)
        
    def export_finished(self, success, msg):
        self.btn_export.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        if success:
            QMessageBox.information(self, "完了", msg)
            self.progress.setValue(100)
        else:
            QMessageBox.warning(self, "キャンセル", msg)
            self.progress.setValue(0)
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_frame()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
