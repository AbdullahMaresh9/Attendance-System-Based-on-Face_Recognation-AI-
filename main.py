import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.database import DatabaseManager
from src.ui.styles import DARK_THEME
from src.ui.login import LoginDialog

def main():
    # Initialize Database
    db = DatabaseManager()
    
    # Create Application
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    
    # Show Login Dialog
    login = LoginDialog()
    if login.exec() == LoginDialog.DialogCode.Accepted:
        # Create Main Window
        window = MainWindow()
        window.show()
        
        # Run Event Loop
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
