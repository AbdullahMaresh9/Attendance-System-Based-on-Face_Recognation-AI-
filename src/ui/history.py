import os
import datetime
import pandas as pd
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QDateEdit, QGroupBox, QMessageBox, QFileDialog, QScroller)
from PyQt6.QtCore import Qt, QDate
from src.database import DatabaseManager

class HistoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 1. Filter Section
        filter_group = QGroupBox("Filter & Reports")
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date)

        self.apply_btn = QPushButton("Show Logs")
        self.apply_btn.clicked.connect(self.load_history)
        self.apply_btn.setStyleSheet("background-color: #3498db; font-weight: bold;")
        filter_layout.addWidget(self.apply_btn)

        filter_layout.addStretch()

        # Quick Report Buttons
        self.daily_report_btn = QPushButton("Daily Report")
        self.daily_report_btn.clicked.connect(lambda: self.generate_report("daily"))
        filter_layout.addWidget(self.daily_report_btn)

        self.weekly_report_btn = QPushButton("Weekly Report")
        self.weekly_report_btn.clicked.connect(lambda: self.generate_report("weekly"))
        filter_layout.addWidget(self.weekly_report_btn)

        self.monthly_report_btn = QPushButton("Monthly Report")
        self.monthly_report_btn.clicked.connect(lambda: self.generate_report("monthly"))
        filter_layout.addWidget(self.monthly_report_btn)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # 2. Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Status", "Mood", "Date", "Time", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        
        # Enable Kinetic Scrolling
        QScroller.grabGesture(self.table, QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        # Status Label
        self.table.verticalHeader().setDefaultSectionSize(100)
        self.status_label = QLabel("Records found: 0")
        layout.addWidget(self.status_label)

        # Load initially
        self.load_history()

    def load_history(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        
        records = self.db.get_attendance_range(start, end)
        self.table.setRowCount(0)
        
        for rec in records:
            rid, name, date, ts, is_active, emotion = rec
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Format time from ISO
            try:
                time_str = datetime.datetime.fromisoformat(ts).strftime("%H:%M:%S")
            except:
                time_str = ts

            status_text = "Active" if is_active == 1 else "Deleted"
            
            self.table.setItem(row, 0, QTableWidgetItem(str(rid)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            
            # Status
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 2, status_item)
            
            # Mood (Emotion)
            mood_item = QTableWidgetItem(emotion or "Neutral")
            if emotion == "Happy": 
                mood_item.setForeground(Qt.GlobalColor.green)
            elif emotion == "Surprised":
                mood_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 3, mood_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(date))
            self.table.setItem(row, 5, QTableWidgetItem(time_str))
            
            # Delete Button
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet("background-color: #c0392b; color: white;")
            del_btn.clicked.connect(lambda checked, r=rid: self.delete_record(r))
            self.table.setCellWidget(row, 6, del_btn)

        self.status_label.setText(f"Records found: {len(records)}")

    def delete_record(self, record_id):
        reply = QMessageBox.question(self, 'Confirm', f"Delete attendance record #{record_id}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_attendance_record(record_id):
                self.load_history()

    def generate_report(self, period):
        today = datetime.datetime.now()
        if period == "daily":
            start = today.strftime("%Y-%m-%d")
            end = start
        elif period == "weekly":
            start = (today - datetime.timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            end = today.strftime("%Y-%m-%d")
        else: # monthly
            start = today.replace(day=1).strftime("%Y-%m-%d")
            end = today.strftime("%Y-%m-%d")

        records = self.db.get_attendance_range(start, end)
        if not records:
            QMessageBox.warning(self, "No Data", f"No records found for the {period} period.")
            return

        df = pd.DataFrame(records, columns=["ID", "Name", "Date", "Timestamp", "IsActive"])
        df['Status'] = df['IsActive'].apply(lambda x: "Active" if x == 1 else "Deleted")
        # Reorder columns for better report
        df = df[["ID", "Name", "Status", "Date", "Timestamp"]]
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", 
                                                 f"Attendance_Report_{period}_{start}.csv", 
                                                 "CSV Files (*.csv)")
        if file_path:
            df.to_csv(file_path, index=False)
            QMessageBox.information(self, "Success", f"Report saved to:\n{file_path}")

    def refresh_data(self):
        self.load_history()
