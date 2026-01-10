from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QGroupBox, QMessageBox, QFileDialog, QFrame)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QImage, QPixmap
import cv2
import face_recognition
import numpy as np
import datetime
from src.database import DatabaseManager
from src.utils import EmailManager
from src.face_engine import FaceEngine
from src.ui.voice import VoiceEngine

class AttendanceVideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, known_face_encodings, known_face_ids, known_face_names, db):
        super().__init__()
        self._run_flag = True
        self.known_face_encodings = known_face_encodings
        self.known_face_ids = known_face_ids
        self.known_face_names = known_face_names
        self.db = db
        self.face_engine = FaceEngine()
        self.voice = VoiceEngine()
        self.last_processed_time = datetime.datetime.now()
        
        # Load settings
        self.num_jitters = int(self.db.get_setting("num_jitters", "1"))
        self.tolerance = float(self.db.get_setting("tolerance", "0.45"))
        self.liveness_enabled = self.db.get_setting("liveness_enabled", "1") == "1"
        
        # Liveness tracking
        self.liveness_status = {} # {user_id: {"blinked": Bool, "frames_closed": Int, "greeted": Bool}}
        self.blink_threshold = 0.26
        self.consecutive_frames = 1
        
        # Stranger tracking
        self.stranger_tracking = {} # {stranger_id_temp: frames_count}
        self.last_stranger_log_time = {} # To avoid rapid duplicate logging
        
        # Emotion smoothing
        self.emotion_history = {} # {user_id: [last_emotions]}

    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                # Process every 500ms
                now = datetime.datetime.now()
                should_process = (now - self.last_processed_time).total_seconds() > 0.5
                
                display_img = cv_img.copy()
                
                if should_process and self.known_face_encodings:
                    self.last_processed_time = now
                    
                    small_frame = cv2.resize(cv_img, (0, 0), fx=0.25, fy=0.25)
                    # Apply CLAHE pre-processing
                    processed_small = self.face_engine.preprocess_image(small_frame)
                    rgb_small_frame = cv2.cvtColor(processed_small, cv2.COLOR_BGR2RGB)
                    
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = self.face_engine.get_face_encodings(rgb_small_frame, face_locations, num_jitters=self.num_jitters)
                    
                    for face_encoding, face_loc in zip(face_encodings, face_locations):
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.tolerance)
                        
                        if True in matches:
                            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            
                            if matches[best_match_index]:
                                user_id = self.known_face_ids[best_match_index]
                                name = self.known_face_names[best_match_index]
                                
                                # Liveness Check
                                if user_id not in self.liveness_status:
                                    self.liveness_status[user_id] = {"blinked": False, "frames_closed": 0, "greeted": False}
                                
                                # Check Liveness if enabled
                                if self.liveness_enabled:
                                    if not self.liveness_status[user_id]["blinked"]:
                                        ear = self.face_engine.check_liveness(rgb_small_frame, face_loc)
                                        if ear < self.blink_threshold:
                                            self.liveness_status[user_id]["frames_closed"] += 1
                                        else:
                                            if self.liveness_status[user_id]["frames_closed"] >= self.consecutive_frames:
                                                self.liveness_status[user_id]["blinked"] = True
                                            self.liveness_status[user_id]["frames_closed"] = 0
                                else:
                                    # Skip blink check if liveness is disabled
                                    self.liveness_status[user_id]["blinked"] = True
                                    self.liveness_status[user_id]["frames_closed"] = 0
                                
                                # Draw status
                                top, right, bottom, left = face_loc
                                top *= 4; right *= 4; bottom *= 4; left *= 4
                                
                                is_live = self.liveness_status[user_id]["blinked"]
                                color = (0, 255, 0) if is_live else (0, 255, 255)
                                # Detect Emotion with temporal smoothing
                                raw_emotion = self.face_engine.detect_emotion(rgb_small_frame, face_loc)
                                if user_id not in self.emotion_history:
                                    self.emotion_history[user_id] = []
                                self.emotion_history[user_id].append(raw_emotion)
                                if len(self.emotion_history[user_id]) > 3:
                                    self.emotion_history[user_id].pop(0)
                                
                                # Majority vote for stable display
                                current_emotion = max(set(self.emotion_history[user_id]), key=self.emotion_history[user_id].count)
                                
                                # Draw status
                                top, right, bottom, left = face_loc
                                top *= 4; right *= 4; bottom *= 4; left *= 4
                                
                                is_live = self.liveness_status[user_id]["blinked"]
                                color = (0, 255, 0) if is_live else (0, 255, 255)
                                status_text = f"{name} ({current_emotion})" if is_live else f"{name} (Please Blink)"
                                
                                cv2.rectangle(display_img, (left, top), (right, bottom), color, 2)
                                cv2.putText(display_img, status_text, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                                # Mark Attendance ONLY if verified
                                if is_live:
                                    success, msg = self.db.mark_attendance(user_id, emotion=current_emotion)
                                    if success and not self.liveness_status[user_id]["greeted"]:
                                        greet_msg = f"Hello {name}, your attendance has been recorded. "
                                        if current_emotion == "Happy":
                                            greet_msg += "You look happy today!"
                                        self.voice.say(greet_msg)
                                        self.liveness_status[user_id]["greeted"] = True
                                    elif not success and msg == "Already registered today" and not self.liveness_status[user_id]["greeted"]:
                                        self.voice.say(f"Hello {name}, you have already registered your attendance today")
                                        self.liveness_status[user_id]["greeted"] = True
                        else:
                            # Stranger detected
                            # We'll use a simple coordinate-based key for temporary tracking
                            top, right, bottom, left = face_loc
                            s_key = f"{top}_{left}" # Not perfect but works for consecutive frames
                            
                            self.stranger_tracking[s_key] = self.stranger_tracking.get(s_key, 0) + 1
                            
                            if self.stranger_tracking[s_key] >= 3: # Seen for 3 cycles (~1.5s)
                                # Log stranger
                                # Draw red box for stranger
                                cv2.rectangle(display_img, (left*4, top*4), (right*4, bottom*4), (0, 0, 255), 2)
                                cv2.putText(display_img, "STRANGER", (left*4, top*4 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                
                                # Crop face for logging
                                face_img = cv_img[top*4:bottom*4, left*4:right*4]
                                if face_img.size > 0:
                                    self.db.log_stranger(face_img)
                                    self.stranger_tracking[s_key] = -10 # cooldown for this spot

                self.change_pixmap_signal.emit(display_img)
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()

class AttendanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.email_manager = EmailManager()
        self.face_engine = FaceEngine()
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.last_processed_time = datetime.datetime.now()
        
        self.init_ui()
        # Check for report on startup 
        self.check_and_send_daily_report()
        
    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Left Side: Camera Feed
        left_layout = QVBoxLayout()
        
        self.feed_group = QGroupBox("Live Attendance Check-in")
        feed_layout = QVBoxLayout()
        
        self.image_label = QLabel("Camera Feed Off")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black; background-color: #eee; min-height: 320px;")
        
        # Scanning Line Overlay
        self.scan_line = QFrame(self.image_label)
        self.scan_line.setStyleSheet("background-color: rgba(46, 204, 113, 100); border: 2px solid #2ecc71;")
        self.scan_line.hide()
        
        self.scan_anim = QPropertyAnimation(self.scan_line, b"geometry")
        self.scan_anim.setDuration(3000)
        self.scan_anim.setLoopCount(-1)
        self.scan_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        feed_layout.addWidget(self.image_label)
        
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Attendance System")
        self.start_btn.clicked.connect(self.start_system)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_system)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        feed_layout.addLayout(btn_layout)
        
        self.status_label = QLabel("Status: Ready")
        feed_layout.addWidget(self.status_label)
        
        self.feed_group.setLayout(feed_layout)
        left_layout.addWidget(self.feed_group)
        
        layout.addLayout(left_layout, stretch=1)
        
        # Right Side: Today's Log
        right_layout = QVBoxLayout()
        self.log_group = QGroupBox("Today's Attendance Log")
        log_layout = QVBoxLayout()
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Name", "Time", "Mood"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        log_layout.addWidget(self.log_table)
        
        refresh_btn = QPushButton("Refresh Log")
        refresh_btn.clicked.connect(self.load_todays_log)
        log_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_log)
        log_layout.addWidget(export_btn)
        
        self.log_group.setLayout(log_layout)
        right_layout.addWidget(self.log_group, stretch=1)
        
        layout.addLayout(right_layout)

    def export_log(self):
        records = self.db.get_attendance_today()
        if not records:
            QMessageBox.information(self, "Info", "No records to export.")
            return
            
        import pandas as pd
        df = pd.DataFrame(records, columns=["Name", "Timestamp", "IsActive", "Mood"])
        df['Status'] = df['IsActive'].apply(lambda x: "Active" if x == 1 else "Deleted")
        # Final export with clean columns
        export_df = df[["Name", "Timestamp", "Status", "Mood"]]
        
        filename, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if filename:
            export_df.to_csv(filename, index=False)
            QMessageBox.information(self, "Success", f"Exported to {filename}")

    def load_known_faces(self):
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        
        encodings_data = self.db.get_all_encodings()
        users = {u[0]: u[1] for u in self.db.get_all_users()}
        
        for user_id, enc_bytes in encodings_data:
            encoding = self.face_engine.decode_from_bytes(enc_bytes)
            self.known_face_encodings.append(encoding)
            self.known_face_ids.append(user_id)
            self.known_face_names.append(users.get(user_id, "Unknown"))
            
        self.status_label.setText(f"Loaded {len(self.known_face_encodings)} face encodings.")

    def start_system(self):
        self.load_known_faces()
        self.video_thread = AttendanceVideoThread(self.known_face_encodings, self.known_face_ids, self.known_face_names, self.db)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()
        self.status_label.setText("Status: Scanning...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Start scanning animation
        self.scan_line.show()
        w = self.image_label.width()
        h = self.image_label.height()
        self.scan_line.setGeometry(0, 0, w, 4)
        self.scan_anim.setStartValue(QRect(0, 0, w, 4))
        self.scan_anim.setEndValue(QRect(0, h-4, w, 4))
        self.scan_anim.start()
        self.load_todays_log()

    def stop_system(self):
        if hasattr(self, 'video_thread'):
            self.video_thread.stop()
        self.status_label.setText("Status: Stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.scan_anim.stop()
        self.scan_line.hide()
        self.image_label.setText("Camera Feed Off")

    def update_image(self, cv_img):
        self.display_image(cv_img)

    def display_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(QPixmap.fromImage(p))

    def load_todays_log(self):
        self.log_table.setRowCount(0)
        records = self.db.get_attendance_today()
        for name, timestamp, is_active, emotion in records:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            
            try:
                time_str = datetime.datetime.fromisoformat(str(timestamp)).strftime("%H:%M:%S")
            except:
                time_str = str(timestamp)
            
            display_name = name if is_active == 1 else f"{name} (Deleted)"
            self.log_table.setItem(row, 0, QTableWidgetItem(display_name))
            self.log_table.setItem(row, 1, QTableWidgetItem(time_str))
            
            mood_item = QTableWidgetItem(emotion or "Neutral")
            if emotion == "Happy":
                mood_item.setForeground(Qt.GlobalColor.green)
            elif emotion == "Surprised":
                mood_item.setForeground(Qt.GlobalColor.yellow)
            self.log_table.setItem(row, 2, mood_item)

    def check_and_send_daily_report(self):
        """Checks if yesterday's report was sent, and sends it if not."""
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        last_sent = self.db.get_setting("last_report_sent_date", "")

        if last_sent != yesterday:
            records = self.db.get_attendance_range(yesterday, yesterday)
            if records:
                print(f"Sending automated daily report for {yesterday}...")
                if self.email_manager.send_daily_report(yesterday, records):
                    self.db.set_setting("last_report_sent_date", yesterday)

    def cleanup(self):
        self.stop_system()

    def hideEvent(self, event):
        self.cleanup()
        super().hideEvent(event)
