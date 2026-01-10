from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QMessageBox, QSlider, QCheckBox)
from PyQt6.QtCore import Qt
from src.database import DatabaseManager

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 1. Security Section
        security_group = QGroupBox("Admin Security")
        sec_layout = QVBoxLayout()
        
        sec_layout.addWidget(QLabel("Current Password:"))
        self.current_pw = QLineEdit()
        self.current_pw.setEchoMode(QLineEdit.EchoMode.Password)
        sec_layout.addWidget(self.current_pw)

        sec_layout.addWidget(QLabel("New Password:"))
        self.new_pw = QLineEdit()
        self.new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        sec_layout.addWidget(self.new_pw)

        self.change_pw_btn = QPushButton("Change Password")
        self.change_pw_btn.clicked.connect(self.change_password)
        self.change_pw_btn.setStyleSheet("background-color: #e67e22; font-weight: bold;")
        sec_layout.addWidget(self.change_pw_btn)
        
        security_group.setLayout(sec_layout)
        layout.addWidget(security_group)

        # 2. Email Section
        email_group = QGroupBox("Email Notification Settings (SMTP)")
        email_layout = QVBoxLayout()

        email_layout.addWidget(QLabel("Sender Email:"))
        self.sender_email = QLineEdit()
        self.sender_email.setText(self.db.get_setting("smtp_user", ""))
        email_layout.addWidget(self.sender_email)

        email_layout.addWidget(QLabel("SMTP Password/App Password:"))
        self.smtp_pw = QLineEdit()
        self.smtp_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_pw.setText(self.db.get_setting("smtp_password", ""))
        email_layout.addWidget(self.smtp_pw)

        email_layout.addWidget(QLabel("Receiver Email:"))
        self.receiver_email = QLineEdit()
        self.receiver_email.setText(self.db.get_setting("receiver_email", ""))
        email_layout.addWidget(self.receiver_email)

        self.save_email_btn = QPushButton("Save Email Settings")
        self.save_email_btn.clicked.connect(self.save_email_settings)
        self.save_email_btn.setStyleSheet("background-color: #3498db; font-weight: bold;")
        email_layout.addWidget(self.save_email_btn)

        email_group.setLayout(email_layout)
        layout.addWidget(email_group)

        # 3. Recognition Tuning
        tuning_group = QGroupBox("Recognition Engine Tuning")
        tuning_layout = QVBoxLayout()

        # Accuracy (Jitters)
        tuning_layout.addWidget(QLabel("Recognition Accuracy (Jitters):"))
        self.jitter_slider = QSlider(Qt.Orientation.Horizontal)
        self.jitter_slider.setRange(1, 10)
        self.jitter_slider.setValue(int(self.db.get_setting("num_jitters", "1")))
        tuning_layout.addWidget(self.jitter_slider)

        # Sensitivity (Tolerance)
        tuning_layout.addWidget(QLabel("Recognition Sensitivity (Tolerance - Lower is Stricter):"))
        self.tolerance_slider = QSlider(Qt.Orientation.Horizontal)
        self.tolerance_slider.setRange(30, 70) # 0.3 to 0.7
        self.tolerance_slider.setValue(int(float(self.db.get_setting("tolerance", "0.45")) * 100))
        tuning_layout.addWidget(self.tolerance_slider)

        # Liveness Toggle
        self.liveness_cb = QCheckBox("Enable Liveness Detection (Blink Check)")
        self.liveness_cb.setChecked(self.db.get_setting("liveness_enabled", "1") == "1")
        tuning_layout.addWidget(self.liveness_cb)

        self.save_tuning_btn = QPushButton("Save Engine Settings")
        self.save_tuning_btn.clicked.connect(self.save_tuning_settings)
        self.save_tuning_btn.setStyleSheet("background-color: #9b59b6; font-weight: bold;")
        tuning_layout.addWidget(self.save_tuning_btn)

        tuning_group.setLayout(tuning_layout)
        layout.addWidget(tuning_group)

        layout.addStretch()

    def change_password(self):
        current = self.current_pw.text()
        new = self.new_pw.text()

        if not current or not new:
            QMessageBox.warning(self, "Warning", "Please fill all fields")
            return

        if self.db.verify_admin_password(current):
            self.db.update_admin_password(new)
            QMessageBox.information(self, "Success", "Password updated successfully!")
            self.current_pw.clear()
            self.new_pw.clear()
        else:
            QMessageBox.critical(self, "Error", "Incorrect current password!")

    def save_tuning_settings(self):
        self.db.set_setting("num_jitters", str(self.jitter_slider.value()))
        self.db.set_setting("tolerance", str(self.tolerance_slider.value() / 100.0))
        self.db.set_setting("liveness_enabled", "1" if self.liveness_cb.isChecked() else "0")
        QMessageBox.information(self, "Success", "Engine settings applied!")

    def save_email_settings(self):
        self.db.set_setting("smtp_user", self.sender_email.text())
        self.db.set_setting("smtp_password", self.smtp_pw.text())
        self.db.set_setting("receiver_email", self.receiver_email.text())
        QMessageBox.information(self, "Success", "Email settings saved!")
