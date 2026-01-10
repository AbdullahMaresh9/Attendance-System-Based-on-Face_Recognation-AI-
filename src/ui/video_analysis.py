import cv2
import os
import numpy as np
import datetime
import face_recognition
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QProgressBar, QFileDialog, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.face_engine import FaceEngine
from src.database import DatabaseManager

class VideoProcessorThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(list) # [(name, time), ...]
    finished_signal = pyqtSignal()

    def __init__(self, file_path, known_face_encodings, known_face_names, db):
        super().__init__()
        self.file_path = file_path
        self.known_face_encodings = known_face_encodings
        self.known_face_names = known_face_names
        self.db = db
        self.face_engine = FaceEngine()
        self._run_flag = True
        
        # Load settings
        self.num_jitters = int(self.db.get_setting("num_jitters", "1"))
        self.tolerance = float(self.db.get_setting("tolerance", "0.45"))
        # For video analysis, we use Higher Upsampling and Lower Skip Rate for better accuracy
        self.upsample = 1 # detect smaller faces
        self.skip_frames = 5 # check more frequently than the default 10

    def run(self):
        cap = cv2.VideoCapture(self.file_path)
        if not cap.isOpened():
            self.finished_signal.emit()
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        results = []
        seen_names = set()
        
        frame_idx = 0
        while self._run_flag:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process every Nth frame
            if frame_idx % self.skip_frames == 0:
                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5) # Scale to 0.5 instead of 0.25 for better detail
                # Apply CLAHE pre-processing
                processed_small = self.face_engine.preprocess_image(small_frame)
                rgb_small_frame = cv2.cvtColor(processed_small, cv2.COLOR_BGR2RGB)
                
                # Use Upsampling to catch smaller faces
                face_locations = face_recognition.face_locations(rgb_small_frame, number_of_times_to_upsample=self.upsample)
                # Use Multi-Jittering for robustness
                face_encodings = self.face_engine.get_face_encodings(rgb_small_frame, face_locations, num_jitters=self.num_jitters)
                
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.tolerance)
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_face_names[first_match_index]
                        
                        # Calculate timestamp in video
                        ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                        time_str = str(datetime.timedelta(milliseconds=ms)).split('.')[0]
                        
                        if name not in seen_names:
                            results.append((name, time_str))
                            seen_names.add(name)
                            self.result_signal.emit(results)

            frame_idx += 1
            if total_frames > 0:
                progress = int((frame_idx / total_frames) * 100)
                self.progress_signal.emit(progress)

        cap.release()
        self.finished_signal.emit()

    def stop(self):
        self._run_flag = False

class VideoAnalysisWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel("Video Analysis (Offline)")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db;")
        layout.addWidget(header)

        # File Select
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label)
        
        self.select_btn = QPushButton("Select Video File")
        self.select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_btn)
        
        layout.addLayout(file_layout)

        # Progress
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Controls
        ctrl_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Analysis")
        self.start_btn.clicked.connect(self.start_analysis)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("background-color: #2ecc71; font-weight: bold; padding: 10px;")
        
        self.stop_btn = QPushButton("Stop Analysis")
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #e74c3c; font-weight: bold; padding: 10px;")
        
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addWidget(self.stop_btn)
        layout.addLayout(ctrl_layout)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name Detected", "First Appearance (Timestamp)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mkv)")
        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.start_btn.setEnabled(True)

    def start_analysis(self):
        # Load known faces
        users = self.db.get_all_users()
        encodings_data = self.db.get_all_encodings()
        
        if not encodings_data:
            QMessageBox.warning(self, "Error", "No registered users found!")
            return

        known_encs = []
        known_names = []
        user_map = {u[0]: u[1] for u in users}
        
        fe = FaceEngine()
        for u_id, enc_blob in encodings_data:
            known_encs.append(fe.decode_from_bytes(enc_blob))
            known_names.append(user_map.get(u_id, "Unknown"))

        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.analysis_thread = VideoProcessorThread(self.file_path, known_encs, known_names, self.db)
        self.analysis_thread.progress_signal.connect(self.progress_bar.setValue)
        self.analysis_thread.result_signal.connect(self.update_table)
        self.analysis_thread.finished_signal.connect(self.on_finished)
        self.analysis_thread.start()

    def stop_analysis(self):
        if hasattr(self, 'analysis_thread') and self.analysis_thread.isRunning():
            self.stop_btn.setEnabled(False)
            self.analysis_thread.stop()
            self.file_label.setText(f"{self.file_label.text()} (Stopping...)")

    def update_table(self, results):
        self.table.setRowCount(0)
        for name, timestamp in results:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(timestamp))

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.file_label.setText(os.path.basename(self.file_path))
        QMessageBox.information(self, "Finished", "Video analysis process ended.")

    def cleanup(self):
        if hasattr(self, 'analysis_thread') and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
            self.analysis_thread.wait()
