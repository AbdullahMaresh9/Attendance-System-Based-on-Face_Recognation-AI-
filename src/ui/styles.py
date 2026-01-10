
DARK_THEME = """
/* General Application Style */
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #444;
    background: #2b2b2b;
}

QTabBar::tab {
    background: #3c3f41;
    color: #bbb;
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #4e5254;
    color: #fff;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover {
    background: #4e5254;
}

/* Group Box */
QGroupBox {
    border: 1px solid #555;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
    color: #3498db;
}

/* Buttons */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #1f618d;
}

QPushButton:disabled {
    background-color: #555;
    color: #888;
}

/* Line Edit & Text Edit */
QLineEdit, QTextEdit {
    background-color: #3c3f41;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 5px;
    color: #fff;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3498db;
}

/* Table Widget */
QTableWidget {
    background-color: #3c3f41;
    gridline-color: #555;
    border: 1px solid #555;
}

QHeaderView::section {
    background-color: #2b2b2b;
    color: #fff;
    padding: 5px;
    border: 1px solid #555;
    font-weight: bold;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #3498db;
}

/* Labels */
QLabel {
    color: #ddd;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #2b2b2b;
    width: 10px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
