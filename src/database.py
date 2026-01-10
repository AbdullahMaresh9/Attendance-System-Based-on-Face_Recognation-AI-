import sqlite3
import datetime
import os
import bcrypt

class DatabaseManager:
    def __init__(self, db_path="data/database.db"):
        self.db_path = db_path
        self._create_dirs()
        self.init_db()

    def _create_dirs(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migration: Add is_active if it doesn't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass # Column already exists

        # Face Encodings table
        # Storing encoding as bytes (blob)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                encoding BLOB NOT NULL,
                image_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        # Strangers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strangers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                count INTEGER DEFAULT 1
            )
        ''')

        # Attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Migration: Add emotion column to attendance if it doesn't exist
        try:
            cursor.execute("ALTER TABLE attendance ADD COLUMN emotion TEXT DEFAULT 'Neutral'")
        except sqlite3.OperationalError:
            pass 

        # Initialize default admin password (default: admin) if not set
        cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
        if not cursor.fetchone():
            default_password = b"admin"
            hashed = bcrypt.hashpw(default_password, bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO settings (key, value) VALUES ('admin_password', ?)", (hashed,))

        conn.commit()
        conn.close()

    def add_user(self, name, phone=None, email=None, address=None, notes=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, phone, email, address, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, phone, email, address, notes))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id

    def update_user(self, user_id, name, phone=None, email=None, address=None, notes=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET name=?, phone=?, email=?, address=?, notes=?
            WHERE id=?
        ''', (name, phone, email, address, notes, user_id))
        conn.commit()
        conn.close()

    def delete_user(self, user_id):
        """Soft delete: just mark as inactive."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_active=0 WHERE id=?', (user_id,))
        conn.commit()
        conn.close()

    def add_encoding(self, user_id, encoding_bytes, image_path=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO encodings (user_id, encoding, image_path)
            VALUES (?, ?, ?)
        ''', (user_id, encoding_bytes, image_path))
        conn.commit()
        conn.close()

    def get_all_users(self):
        """Returns only active users."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_active=1')
        users = cursor.fetchall()
        conn.close()
        return users

    def get_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    def get_all_encodings(self):
        """Returns a list of tuples: (user_id, encoding_blob) for active users only."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.user_id, e.encoding 
            FROM encodings e
            JOIN users u ON e.user_id = u.id
            WHERE u.is_active = 1
        ''')
        data = cursor.fetchall()
        conn.close()
        return data

    def mark_attendance(self, user_id, emotion="Neutral"):
        """Marks attendance for a user, prevents duplicates, and stores emotion."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if already present today
        cursor.execute("SELECT id FROM attendance WHERE user_id = ? AND date = ?", (user_id, today))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return False, "Already registered today"

        try:
            cursor.execute("INSERT INTO attendance (user_id, date, timestamp, emotion) VALUES (?, ?, ?, ?)",
                         (user_id, today, now_ts, emotion))
            conn.commit()
            conn.close()
            return True, "Attendance marked"
        except Exception as e:
            conn.close()
            return False, str(e)

    def get_attendance_range(self, start_date, end_date):
        """Returns records between two dates (inclusive), including user status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.id, u.name, a.date, a.timestamp, u.is_active, a.emotion
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.date BETWEEN ? AND ?
            ORDER BY a.date DESC, a.timestamp DESC
        ''', (start_date, end_date))
        records = cursor.fetchall()
        conn.close()
        return records

    def delete_attendance_record(self, record_id):
        """Removes a specific attendance log entry."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        return True, "Attendance record deleted"

    def get_attendance_stats(self):
        """Returns (total_active_users, present_today, absence_today)"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active=1")
        total_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT a.user_id) 
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.date = ? AND u.is_active = 1
        ''', (today,))
        present_today = cursor.fetchone()[0]
        
        conn.close()
        return total_users, present_today, total_users - present_today

    def get_mood_stats(self):
        """Returns emotion counts for today's attendance."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT emotion, COUNT(*) FROM attendance 
            WHERE date = ? 
            GROUP BY emotion
        ''', (today,))
        stats = cursor.fetchall()
        conn.close()
        return stats

    def get_attendance_today(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.name, a.timestamp, u.is_active, a.emotion
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.date = ?
            ORDER BY a.timestamp DESC
        ''', (today,))
        records = cursor.fetchall()
        conn.close()
        return records

    def get_peak_hours(self):
        """Returns list of (hour, count)"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) 
            FROM attendance 
            WHERE date = ?
            GROUP BY hour
            ORDER BY hour ASC
        ''', (today,))
        data = cursor.fetchall()
        conn.close()
        return data

    def get_top_disciplined(self, limit=5):
        """Returns list of (name, count) for the last 30 days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.name, COUNT(a.id) as count
            FROM users u
            JOIN attendance a ON u.id = a.user_id
            GROUP BY u.id
            ORDER BY count DESC
            LIMIT ?
        ''', (limit,))
        data = cursor.fetchall()
        conn.close()
        return data

    def verify_admin_password(self, password):
        """Verifies if the provided password matches the stored hash."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='admin_password'")
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stored_hash = result[0].encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
        return False

    def update_admin_password(self, new_password):
        """Updates the admin password with a new hash."""
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value=? WHERE key='admin_password'", (hashed,))
        conn.commit()
        conn.close()
        return True

    def get_setting(self, key, default=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default

    def set_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    def log_stranger(self, image_data):
        """Logs a stranger or updates their last seen."""
        # Save image to a 'strangers' folder
        os.makedirs("data/strangers", exist_ok=True)
        filename = f"stranger_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join("data/strangers", filename)
        
        import cv2
        cv2.imwrite(filepath, image_data)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO strangers (image_path, first_seen, last_seen, count)
            VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        ''', (filepath,))
        conn.commit()
        conn.close()
        return True

    def get_all_strangers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM strangers ORDER BY last_seen DESC")
        data = cursor.fetchall()
        conn.close()
        return data

    def delete_stranger(self, stranger_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Get path for cleanup
        cursor.execute("SELECT image_path FROM strangers WHERE id=?", (stranger_id,))
        row = cursor.fetchone()
        if row and os.path.exists(row[0]):
            try:
                os.remove(row[0])
            except:
                pass
            
        cursor.execute("DELETE FROM strangers WHERE id=?", (stranger_id,))
        conn.commit()
        conn.close()
        return True
