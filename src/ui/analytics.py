import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox)
from PyQt6.QtCore import Qt
from src.database import DatabaseManager

# Matplotlib integration
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AnalyticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 1. Summary Cards
        summary_layout = QHBoxLayout()
        self.total_card = self.create_summary_card("Total Users", "0", "#3498db")
        self.present_card = self.create_summary_card("Present Today", "0", "#2ecc71")
        self.absent_card = self.create_summary_card("Absent Today", "0", "#e74c3c")
        
        summary_layout.addWidget(self.total_card)
        summary_layout.addWidget(self.present_card)
        summary_layout.addWidget(self.absent_card)
        self.layout.addLayout(summary_layout)

        # 2. Charts Area
        charts_layout = QHBoxLayout()
        
        # Pie Chart Container
        self.pie_canvas = FigureCanvas(Figure(figsize=(5, 4), facecolor='#2b2b2b'))
        pie_group = QGroupBox("Daily Attendance Ratio")
        pie_vbox = QVBoxLayout()
        pie_vbox.addWidget(self.pie_canvas)
        pie_group.setLayout(pie_vbox)
        charts_layout.addWidget(pie_group)

        # Bar Chart Container
        self.bar_canvas = FigureCanvas(Figure(figsize=(5, 4), facecolor='#2b2b2b'))
        bar_group = QGroupBox("Peak Attendance Hours")
        bar_vbox = QVBoxLayout()
        bar_vbox.addWidget(self.bar_canvas)
        bar_group.setLayout(bar_vbox)
        charts_layout.addWidget(bar_group)

        # 3. Mood Chart Container
        self.mood_canvas = FigureCanvas(Figure(figsize=(5, 4), facecolor='#2b2b2b'))
        mood_group = QGroupBox("Mood of the Day")
        mood_vbox = QVBoxLayout()
        mood_vbox.addWidget(self.mood_canvas)
        mood_group.setLayout(mood_vbox)
        charts_layout.addWidget(mood_group)

        self.layout.addLayout(charts_layout)

        # 3. Top Disciplined Table
        table_group = QGroupBox("Top Disciplined (Last 30 Days)")
        table_layout = QVBoxLayout()
        self.top_table = QTableWidget()
        self.top_table.setColumnCount(2)
        self.top_table.setHorizontalHeaderLabels(["Name", "Total Check-ins"])
        self.top_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.top_table)
        table_group.setLayout(table_layout)
        self.layout.addWidget(table_group)

        # Initial Refresh
        self.refresh_data()

    def create_summary_card(self, title, value, color):
        card = QGroupBox()
        card.setStyleSheet(f"QGroupBox {{ border: 2px solid {color}; border-radius: 10px; background-color: #3c3f41; }}")
        vbox = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; color: #bbb;")
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        
        vbox.addWidget(title_label)
        vbox.addWidget(value_label)
        card.setLayout(vbox)
        
        # Store label for updates
        card.value_label = value_label
        return card

    def refresh_data(self):
        # 1. Update Cards
        total, present, absent = self.db.get_attendance_stats()
        self.total_card.value_label.setText(str(total))
        self.present_card.value_label.setText(str(present))
        self.absent_card.value_label.setText(str(absent))

        # 2. Update Pie Chart
        self.update_pie_chart(present, absent)

        # 3. Update Bar Chart
        peak_data = self.db.get_peak_hours()
        self.update_bar_chart(peak_data)

        # 4. Update Mood Chart
        mood_data = self.db.get_mood_stats()
        self.update_mood_chart(mood_data)

        # 5. Update Table
        top_users = self.db.get_top_disciplined()
        self.top_table.setRowCount(0)
        for name, count in top_users:
            row = self.top_table.rowCount()
            self.top_table.insertRow(row)
            self.top_table.setItem(row, 0, QTableWidgetItem(name))
            self.top_table.setItem(row, 1, QTableWidgetItem(str(count)))

    def update_pie_chart(self, present, absent):
        self.pie_canvas.figure.clear()
        ax = self.pie_canvas.figure.add_subplot(111)
        
        if present == 0 and absent == 0:
            ax.text(0.5, 0.5, 'No Data Today', transform=ax.transAxes, ha='center', color='white')
        else:
            labels = ['Present', 'Absent']
            sizes = [present, absent]
            colors = ['#2ecc71', '#e74c3c']
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'color':"w"})
        
        self.pie_canvas.draw()

    def update_bar_chart(self, peak_data):
        self.bar_canvas.figure.clear()
        ax = self.bar_canvas.figure.add_subplot(111)
        
        if not peak_data:
            ax.text(0.5, 0.5, 'No Attendance Yet', transform=ax.transAxes, ha='center', color='white')
        else:
            hours = [d[0] for d in peak_data]
            counts = [d[1] for d in peak_data]
            ax.bar(hours, counts, color='#3498db')
            ax.set_xlabel('Hour of Day', color='white')
            ax.set_ylabel('Check-ins', color='white')
            ax.tick_params(colors='white')
            ax.set_facecolor('#2b2b2b')
        
        self.bar_canvas.draw()
    def update_mood_chart(self, mood_data):
        self.mood_canvas.figure.clear()
        ax = self.mood_canvas.figure.add_subplot(111)
        
        if not mood_data:
            ax.text(0.5, 0.5, 'Waiting for Check-ins...', transform=ax.transAxes, ha='center', color='white')
        else:
            labels = [d[0] for d in mood_data]
            counts = [d[1] for d in mood_data]
            colors = []
            for lab in labels:
                if lab == "Happy": colors.append('#2ecc71')
                elif lab == "Neutral": colors.append('#3498db')
                elif lab == "Surprised": colors.append('#f1c40f')
                else: colors.append('#95a5a6')
                
            ax.bar(labels, counts, color=colors)
            ax.set_ylabel('Count', color='white')
            ax.tick_params(colors='white')
            ax.set_facecolor('#2b2b2b')
        
        self.mood_canvas.draw()
