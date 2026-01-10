from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                              QLabel, QStatusBar, QScrollArea)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect
import sys

from src.ui.dashboard import DashboardWidget
from src.ui.testing import TestingWidget
from src.ui.attendance import AttendanceWidget
from src.ui.analytics import AnalyticsWidget
from src.ui.history import HistoryWidget
from src.ui.settings import SettingsWidget
from src.ui.video_analysis import VideoAnalysisWidget
from src.ui.strangers import StrangerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition System")
        self.setGeometry(100, 100, 1200, 800)
        
        self.init_ui()

    def init_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Initialize Tab Widgets
        self.dashboard_tab = DashboardWidget()
        self.testing_tab = TestingWidget()
        self.attendance_tab = AttendanceWidget()
        self.analytics_tab = AnalyticsWidget()
        self.history_tab = HistoryWidget()
        self.settings_tab = SettingsWidget()
        self.video_analysis_tab = VideoAnalysisWidget()
        self.strangers_tab = StrangerWidget()
        
        # Helper to create styled scroll area
        def wrap_scroll(widget):
            scroll = QScrollArea()
            scroll.setWidget(widget)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            scroll.setStyleSheet("background-color: transparent;")
            # Enable kinetic scrolling for the scroll area itself
            from PyQt6.QtWidgets import QScroller
            QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
            return scroll

        # Add Tabs (Wrapped in Scroll Areas where needed)
        self.tabs.addTab(wrap_scroll(self.dashboard_tab), "Identity Management")
        self.tabs.addTab(self.testing_tab, "Model Testing")
        self.tabs.addTab(self.attendance_tab, "Attendance System")
        self.tabs.addTab(wrap_scroll(self.analytics_tab), "Analytics")
        self.tabs.addTab(self.history_tab, "Attendance Logs")
        self.tabs.addTab(wrap_scroll(self.settings_tab), "Settings")
        self.tabs.addTab(self.video_analysis_tab, "Video Analysis")
        self.tabs.addTab(self.strangers_tab, "Strangers")
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("System Ready")

        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_change)

    def set_status(self, message):
        self.status_bar.showMessage(message)

    def on_tab_change(self, index):
        # 1. Handle background cleanup/refresh
        if index != 1:
            self.testing_tab.cleanup()
        if index != 2:
            self.attendance_tab.cleanup()
            
        if self.tabs.tabText(index) == "Analytics":
            self.analytics_tab.refresh_data()
        elif self.tabs.tabText(index) == "Attendance Logs":
            self.history_tab.refresh_data()
        elif self.tabs.tabText(index) == "Strangers":
            self.strangers_tab.refresh_data()

        # 2. Add sliding animation
        current_widget = self.tabs.widget(index)
        if current_widget:
            try:
                # Subtle slide from bottom
                if not hasattr(self, 'pos_anim'):
                    self.pos_anim = QPropertyAnimation(current_widget, b"pos")
                else:
                    self.pos_anim.stop()
                    self.pos_anim.setTargetObject(current_widget)
                    
                self.pos_anim.setDuration(300)
                self.pos_anim.setStartValue(QPoint(0, 30))
                self.pos_anim.setEndValue(QPoint(0, 0))
                self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.pos_anim.start()
            except Exception as e:
                print(f"Animation Error: {e}")

    def closeEvent(self, event):
        self.testing_tab.cleanup()
        self.attendance_tab.cleanup()
        self.video_analysis_tab.cleanup()
        event.accept()
