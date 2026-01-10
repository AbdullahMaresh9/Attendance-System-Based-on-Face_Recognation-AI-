from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog, 
                             QLabel, QLineEdit, QTextEdit, QFileDialog, QMessageBox,
                             QGroupBox, QFormLayout, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from src.database import DatabaseManager
from src.face_engine import FaceEngine

class CameraWidget(QWidget):
    image_captured = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.video_label = QLabel("Camera Feed")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setStyleSheet("border: 1px solid black; background-color: #eee;")
        self.layout.addWidget(self.video_label)
        
        self.capture_btn = QPushButton("Capture Photo")
        self.capture_btn.clicked.connect(self.capture_image)
        self.layout.addWidget(self.capture_btn)
        
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
    def start_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
        self.timer.start(30)
        
    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
            
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            # Convert to Qt format
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            p = convert_to_Qt_format.scaled(320, 240, Qt.AspectRatioMode.KeepAspectRatio)
            self.video_label.setPixmap(QPixmap.fromImage(p))
            
    def capture_image(self):
        if hasattr(self, 'current_frame'):
            self.image_captured.emit(self.current_frame)
            self.stop_camera()

class AddUserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.user_data = user_data # If not None, we are in Edit Mode
        self.setWindowTitle("Edit Person" if self.user_data else "Add New Person")
        self.setModal(True)
        self.resize(600, 500)
        
        self.db = DatabaseManager()
        self.face_engine = FaceEngine()
        self.captured_images = [] # List of numpy arrays
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Scroll Area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Form
        form_group = QGroupBox("Personal Details")
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        
        form_layout.addRow("Full Name *:", self.name_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("Notes:", self.notes_input)
        
        if self.user_data:
            # Pre-fill data
            # user_data structure: (id, name, phone, email, address, notes, created_at)
            self.name_input.setText(self.user_data[1])
            self.phone_input.setText(self.user_data[2] if self.user_data[2] else "")
            self.email_input.setText(self.user_data[3] if self.user_data[3] else "")
            self.address_input.setText(self.user_data[4] if self.user_data[4] else "")
            self.notes_input.setText(self.user_data[5] if self.user_data[5] else "")
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Image Capture
        image_group = QGroupBox("Face Registration")
        image_layout = QVBoxLayout()
        
        self.camera_widget = CameraWidget()
        self.camera_widget.image_captured.connect(self.on_image_captured)
        image_layout.addWidget(self.camera_widget)
        
        btn_layout = QHBoxLayout()
        self.start_cam_btn = QPushButton("Start Camera")
        self.start_cam_btn.clicked.connect(self.camera_widget.start_camera)
        btn_layout.addWidget(self.start_cam_btn)
        
        self.upload_btn = QPushButton("Upload Image")
        self.upload_btn.clicked.connect(self.upload_image)
        btn_layout.addWidget(self.upload_btn)
        
        image_layout.addLayout(btn_layout)
        
        self.images_label = QLabel("Captured Images: 0")
        image_layout.addWidget(self.images_label)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Dialog Buttons (Fixed at bottom)
        dialog_btns = QHBoxLayout()
        self.save_btn = QPushButton("Save Person")
        self.save_btn.clicked.connect(self.save_user)
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet("background-color: #2ecc71; font-weight: bold;")
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        
        dialog_btns.addStretch()
        dialog_btns.addWidget(self.cancel_btn)
        dialog_btns.addWidget(self.save_btn)
        main_layout.addLayout(dialog_btns)

    def on_image_captured(self, image):
        self.captured_images.append(image)
        self.images_label.setText(f"Captured Images: {len(self.captured_images)}")
        QMessageBox.information(self, "Success", "Image captured! You can capture more or save now.")
        # Restart camera for more captures if needed, or let user click start again
        # self.camera_widget.start_camera() 

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            from src.utils import load_image_safe
            image = load_image_safe(file_path)
            if image is not None:
                self.captured_images.append(image)
                self.images_label.setText(f"Captured Images: {len(self.captured_images)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load image. Please check the file format and path.")

    def save_user(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return
            
        # If adding new user, require at least one image
        if not self.user_data and not self.captured_images:
            QMessageBox.warning(self, "Validation Error", "At least one face image is required for new users.")
            return
            
        # Process images and encodings (if any new images captured)
        encodings = []
        for img in self.captured_images:
            # Convert BGR to RGB for face_recognition
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            found_encodings = self.face_engine.get_face_encodings(rgb_img)
            if found_encodings:
                encodings.append(found_encodings[0]) # Take the first face found
        
        if not self.user_data and not encodings:
             # If new user and captured images yielded no faces
            QMessageBox.critical(self, "Error", "No faces detected in the captured images. Please try again.")
            return

        if self.captured_images and not encodings:
            # If editing and tried to add images but none worked
            QMessageBox.warning(self, "Warning", "Captured images contained no detectable faces. User details will be updated, but no new photos added.")

        # Save to DB
        try:
            if self.user_data:
                # Update existing user
                user_id = self.user_data[0]
                self.db.update_user(
                    user_id,
                    name,
                    self.phone_input.text(),
                    self.email_input.text(),
                    self.address_input.text(),
                    self.notes_input.toPlainText()
                )
                msg = f"User {name} updated successfully!"
            else:
                # Add new user
                user_id = self.db.add_user(
                    name, 
                    self.phone_input.text(),
                    self.email_input.text(),
                    self.address_input.text(),
                    self.notes_input.toPlainText()
                )
                msg = f"User {name} added successfully!"
            
            # Add new encodings if any
            for enc in encodings:
                enc_bytes = self.face_engine.encode_to_bytes(enc)
                self.db.add_encoding(user_id, enc_bytes)
                
            QMessageBox.information(self, "Success", msg)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        self.camera_widget.stop_camera()
        event.accept()

    def reject(self):
        self.camera_widget.stop_camera()
        super().reject()

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Top Bar
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name...")
        self.search_input.textChanged.connect(self.filter_users)
        top_layout.addWidget(self.search_input)
        
        self.add_btn = QPushButton("Add New Person")
        self.add_btn.clicked.connect(self.open_add_user_dialog)
        top_layout.addWidget(self.add_btn)
        
        layout.addLayout(top_layout)
        
        # User Table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Actions"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.user_table)

    def load_users(self):
        self.user_table.setRowCount(0)
        users = self.db.get_all_users()
        for user in users:
            self.add_user_to_table(user)

    def add_user_to_table(self, user):
        row = self.user_table.rowCount()
        self.user_table.insertRow(row)
        
        # ID, Name, Phone
        self.user_table.setItem(row, 0, QTableWidgetItem(str(user[0])))
        self.user_table.setItem(row, 1, QTableWidgetItem(user[1]))
        self.user_table.setItem(row, 2, QTableWidgetItem(user[2] if user[2] else ""))
        
        # Actions
        action_widget = QWidget()
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self.edit_user(user[0]))
        action_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_user(user[0]))
        action_layout.addWidget(delete_btn)
        
        action_widget.setLayout(action_layout)
        self.user_table.setCellWidget(row, 3, action_widget)

    def filter_users(self):
        text = self.search_input.text().lower()
        for row in range(self.user_table.rowCount()):
            name_item = self.user_table.item(row, 1)
            if text in name_item.text().lower():
                self.user_table.setRowHidden(row, False)
            else:
                self.user_table.setRowHidden(row, True)

    def open_add_user_dialog(self):
        dialog = AddUserDialog(self)
        if dialog.exec():
            self.load_users()

    def edit_user(self, user_id):
        user = self.db.get_user(user_id)
        if user:
            dialog = AddUserDialog(self, user_data=user)
            if dialog.exec():
                self.load_users()

    def delete_user(self, user_id):
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     "Are you sure you want to delete this user? This cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_user(user_id)
            self.load_users()
