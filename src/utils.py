import yagmail
import datetime
import os
from src.database import DatabaseManager
import cv2
import numpy as np

def load_image_safe(image_path):
    """Loads an image safely even if path contains non-ASCII characters."""
    try:
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

class EmailManager:
    def __init__(self):
        self.db = DatabaseManager()

    def send_report(self, subject, body, attachment_path=None):
        """Sends an email with an optional attachment."""
        user = self.db.get_setting("smtp_user")
        password = self.db.get_setting("smtp_password")
        receiver = self.db.get_setting("receiver_email")

        if not all([user, password, receiver]):
            print("Email configuration missing. Cannot send report.")
            return False

        try:
            yag = yagmail.SMTP(user, password)
            if attachment_path and os.path.exists(attachment_path):
                yag.send(to=receiver, subject=subject, contents=[body, attachment_path])
            else:
                yag.send(to=receiver, subject=subject, contents=body)
            return True
        except Exception as e:
            print(f"Email Error: {e}")
            return False

    def send_daily_report(self, date_str, records):
        """Generates and sends the daily summary report."""
        if not records:
            return False

        subject = f"Face Recognition Attendance Report - {date_str}"
        body = f"Hello Administrator,\n\nHere is the attendance report for {date_str}.\n"
        body += f"Total attendees: {len(records)}\n\n"
        body += "Best regards,\nAttendance System"

        # Create temporary CSV
        import pandas as pd
        df = pd.DataFrame(records, columns=["ID", "Name", "Date", "Timestamp", "IsActive", "Mood"])
        df['Status'] = df['IsActive'].apply(lambda x: "Active" if x == 1 else "Deleted")
        temp_file = f"temp_report_{date_str}.csv"
        df[["ID", "Name", "Status", "Mood", "Date", "Timestamp"]].to_csv(temp_file, index=False)

        success = self.send_report(subject, body, temp_file)
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        return success
