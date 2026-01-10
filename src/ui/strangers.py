from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QScroller)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from src.database import DatabaseManager
import os

class StrangerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Stranger Tracking Log")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c;")
        header_layout.addWidget(title)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_strangers)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Photo", "First Seen", "Last Seen", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(100)
        layout.addWidget(self.table)
        
        # Kinetic Scrolling
        QScroller.grabGesture(self.table, QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        self.load_strangers()

    def load_strangers(self):
        records = self.db.get_all_strangers()
        self.table.setRowCount(0)
        
        for rec in records:
            sid, img_path, first, last, count = rec
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Photo
            img_label = QLabel()
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                img_label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                img_label.setText("No Image")
            self.table.setCellWidget(row, 0, img_label)
            
            self.table.setItem(row, 1, QTableWidgetItem(first))
            self.table.setItem(row, 2, QTableWidgetItem(last))
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet("background-color: #c0392b; color: white;")
            del_btn.clicked.connect(lambda checked, i=sid: self.delete_stranger(i))
            action_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 3, action_widget)

    def delete_stranger(self, sid):
        if self.db.delete_stranger(sid):
            self.load_strangers()

    def refresh_data(self):
        self.load_strangers()
