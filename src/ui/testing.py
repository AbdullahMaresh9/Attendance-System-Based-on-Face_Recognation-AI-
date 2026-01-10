from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QTextEdit, QTabWidget, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QScroller)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
import face_recognition
import numpy as np
from src.database import DatabaseManager
from src.face_engine import FaceEngine
from src.ui.voice import VoiceEngine

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, known_face_encodings, known_face_names):
        super().__init__()
        self._run_flag = True
        self.known_face_encodings = known_face_encodings
        self.known_face_names = known_face_names
        self.face_engine = FaceEngine()
        self.voice = VoiceEngine()
        
        # Liveness tracking
        self.liveness_status = {}
        self.blink_threshold = 0.26 
        self.consecutive_frames = 1

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # Process frame here
                small_frame = cv2.resize(cv_img, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                for face_encoding, face_location in zip(face_encodings, face_locations):
                    # Use stricter tolerance from FaceEngine
                    tolerance = FaceEngine.DEFAULT_TOLERANCE
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=tolerance)
                    name = "Unknown"
                    distance = 0.0
                    liveness_label = ""

                    if self.known_face_encodings:
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index]
                            distance = face_distances[best_match_index]
                            
                            # Liveness Check for known faces
                            # Initialize status if new
                            if name not in self.liveness_status:
                                self.liveness_status[name] = {"blinked": False, "frames_closed": 0, "greeted": False}
                            
                            if not self.liveness_status[name]["blinked"]:
                                # Get EAR
                                ear = self.face_engine.check_liveness(rgb_small_frame, face_location)
                                if ear < self.blink_threshold:
                                    self.liveness_status[name]["frames_closed"] += 1
                                else:
                                    if self.liveness_status[name]["frames_closed"] >= self.consecutive_frames:
                                        self.liveness_status[name]["blinked"] = True
                                        if not self.liveness_status[name]["greeted"]:
                                            self.voice.say(f"Verification successful, Welcome {name}")
                                            self.liveness_status[name]["greeted"] = True
                                    self.liveness_status[name]["frames_closed"] = 0
                                
                                liveness_label = " (Please Blink)" if not self.liveness_status[name]["blinked"] else " (Verified)"
                            else:
                                liveness_label = " (Verified)"

                    face_names.append((name, distance, liveness_label))
                
                # Draw results on the frame
                for ((top, right, bottom, left), (name, dist, live_text)) in zip(face_locations, face_names):
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    is_verified = "(Verified)" in live_text or name == "Unknown"
                    color = (0, 255, 0) if is_verified and name != "Unknown" else (0, 0, 255)
                    if name != "Unknown" and "(Please Blink)" in live_text:
                        color = (0, 255, 255) # Yellow for pending
                    
                    cv2.rectangle(cv_img, (left, top), (right, bottom), color, 2)
                    cv2.rectangle(cv_img, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                    
                    label = f"{name}{live_text}"
                    if name != "Unknown":
                        label += f" [{dist:.2f}]"
                        
                    cv2.putText(cv_img, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

                self.change_pixmap_signal.emit(cv_img)
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

class LiveRecognitionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.face_engine = FaceEngine()
        self.known_face_encodings = []
        self.known_face_names = []
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Live Recognition")
        self.start_btn.clicked.connect(self.start_video)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Video Feed
        self.image_label = QLabel("Camera Feed Off")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black; background-color: #eee; min-height: 480px;")
        layout.addWidget(self.image_label)
        
        # Stats
        self.stats_label = QLabel("Status: Ready")
        layout.addWidget(self.stats_label)

    def load_known_faces(self):
        """Loads all known faces from DB for recognition."""
        self.known_face_encodings = []
        self.known_face_names = []
        
        encodings_data = self.db.get_all_encodings()
        users = {u[0]: u[1] for u in self.db.get_all_users()}
        
        for user_id, enc_bytes in encodings_data:
            encoding = self.face_engine.decode_from_bytes(enc_bytes)
            self.known_face_encodings.append(encoding)
            self.known_face_names.append(users.get(user_id, "Unknown"))
            
        self.stats_label.setText(f"Loaded {len(self.known_face_encodings)} face encodings.")

    def start_video(self):
        self.load_known_faces()
        self.video_thread = VideoThread(self.known_face_encodings, self.known_face_names)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_video(self):
        if hasattr(self, 'video_thread'):
            self.video_thread.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.image_label.setText("Camera Feed Off")

    def cleanup(self):
        self.stop_video()

    def update_image(self, cv_img):
        self.display_image(cv_img)

    def display_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(QPixmap.fromImage(p))


class BatchTestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Top controls
        top_layout = QHBoxLayout()
        btn = QPushButton("Upload Image for Testing")
        btn.clicked.connect(self.upload_image)
        top_layout.addWidget(btn)
        layout.addLayout(top_layout)
        
        # Main Content Area (Split View)
        content_layout = QHBoxLayout()
        
        # Left: Image Display
        self.image_label = QLabel("No Image Uploaded")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0; min-width: 400px; min-height: 400px;")
        content_layout.addWidget(self.image_label, stretch=1)
        
        # Right: Results List
        results_group = QGroupBox("Identified People")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["#", "Name", "Phone", "Email", "Notes"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        results_layout.addWidget(self.results_table)
        
        # Kinetic Scrolling
        QScroller.grabGesture(self.results_table, QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        
        results_group.setLayout(results_layout)
        content_layout.addWidget(results_group, stretch=1)
        
        layout.addLayout(content_layout)

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if not file_path:
            return

        from src.utils import load_image_safe
        image = load_image_safe(file_path)
        
        if image is None:
            QMessageBox.warning(self, "Error", "Could not load image.")
            return

        # Clear previous results
        self.results_table.setRowCount(0)
        self.image_label.setText("Processing...")
        
        # Process image
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        # Load known faces
        db = DatabaseManager()
        face_engine = FaceEngine()
        known_encodings = []
        known_ids = []
        
        encodings_data = db.get_all_encodings()
        # We need user details, not just names
        # Create a map: user_id -> user_details_tuple
        users_map = {u[0]: u for u in db.get_all_users()}
        
        for user_id, enc_bytes in encodings_data:
            known_encodings.append(face_engine.decode_from_bytes(enc_bytes))
            known_ids.append(user_id)

        # Match faces
        display_image = image.copy()
        
        for idx, (face_encoding, face_loc) in enumerate(zip(face_encodings, face_locations)):
            tolerance = FaceEngine.DEFAULT_TOLERANCE
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=tolerance)
            user_details = None
            name = "Unknown"
            
            if known_encodings:
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    user_id = known_ids[best_match_index]
                    user_details = users_map.get(user_id)
                    if user_details:
                        name = user_details[1]
            
            # Draw on image
            top, right, bottom, left = face_loc
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(display_image, (left, top), (right, bottom), color, 2)
            
            # Draw number badge
            badge_text = str(idx + 1)
            cv2.circle(display_image, (left, top), 15, color, -1)
            cv2.putText(display_image, badge_text, (left - 5, top + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Add to table
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(badge_text))
            self.results_table.setItem(row, 1, QTableWidgetItem(name))
            
            if user_details:
                self.results_table.setItem(row, 2, QTableWidgetItem(user_details[2] if user_details[2] else ""))
                self.results_table.setItem(row, 3, QTableWidgetItem(user_details[3] if user_details[3] else ""))
                self.results_table.setItem(row, 4, QTableWidgetItem(user_details[5] if user_details[5] else ""))
            else:
                self.results_table.setItem(row, 2, QTableWidgetItem("-"))
                self.results_table.setItem(row, 3, QTableWidgetItem("-"))
                self.results_table.setItem(row, 4, QTableWidgetItem("-"))

        # Display Image
        rgb_disp = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_disp.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_disp.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Scale to fit label while keeping aspect ratio
        pixmap = QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

class TestingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        tabs = QTabWidget()
        self.live_tab = LiveRecognitionWidget()
        self.batch_tab = BatchTestWidget()
        
        tabs.addTab(self.live_tab, "Live Recognition")
        tabs.addTab(self.batch_tab, "Batch Testing")
        
        layout.addWidget(tabs)

    def cleanup(self):
        """Stops any running video threads."""
        self.live_tab.cleanup()

    def hideEvent(self, event):
        """Stop camera when widget is hidden (e.g. tab switch)."""
        self.cleanup()
        super().hideEvent(event)
