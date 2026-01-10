from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from src.database import DatabaseManager

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setWindowTitle("Admin Login")
        self.setFixedSize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Enter Admin Password:"))
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        self.login_btn.setStyleSheet("background-color: #27ae60; font-weight: bold; padding: 10px;")
        layout.addWidget(self.login_btn)

        layout.addStretch()

    def handle_login(self):
        password = self.password_input.text()
        if self.db.verify_admin_password(password):
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Invalid password!")
            self.password_input.clear()
