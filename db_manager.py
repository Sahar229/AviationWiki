import sqlite3
import hashlib
import threading

class DatabaseManager:
    """
    מחלקה לניהול בסיס הנתונים
    משתמשת במנגנון נעילה כדי להבטיח עבודה בטוחה בסביבה מרובת תהליכונים
    """
    def __init__(self, db_name="users.db"):
        self.db_name = db_name
        self.lock = threading.Lock()
        
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
        print("[*] Database ready.")

    def hash_password(self, password: str) -> str:
        """
        פונקציית עזר להצפנת סיסמה. מקבלת סיסמה כטקסט גלוי ומחזירה אותה מוצפנת.
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def login(self, email: str, password: str):
        """
        פונקציה לבדיקת התחברות משתמש.
        מחפשת במסד הנתונים משתמש עם האימייל והסיסמה שסופקו.
        מחזירה טאפל המכיל את אם נמצאה התאמה, או כלום אם לא.
        """
        hashed_pw = self.hash_password(password)
        user = None
        
        with self.lock:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id, username FROM users WHERE email=? AND password=?", 
                               (email, hashed_pw))
                user = cursor.fetchone()
            finally:
                conn.close() # סגירה בטוחה בתוך ה-finally
        return user

    def register(self, username: str, email: str, password: str):
        """
        פונקציה לרישום משתמש חדש לבסיס הנתונים.
        מבצעת שמירה של הנתונים ומוודאת שאין כפילויות.
        מחזירה מילון עם מפתח 'status' והודעת שגיאה במקרה הצורך.
        """
        hashed_pw = self.hash_password(password)
        response_data = {}
        
        with self.lock:
            conn = sqlite3.connect(self.db_name) # פתיחה בתוך הפונקציה
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                               (username, email, hashed_pw))
                conn.commit()
                response_data = {"status": "ok"}
                print(f"Created new user: {username}")
            except sqlite3.IntegrityError as e:
                error_message = str(e).lower()
                if "username" in error_message:
                    response_data = {"status": "fail", "error": "Username Already Exists"}
                elif "email" in error_message:
                    response_data = {"status": "fail", "error": "Email Already Exists"}
                else:
                    response_data = {"status": "fail", "error": "Username or Email Already Exists"}
            except Exception as e:
                response_data = {"status": "fail", "error": f"General error: {e}"}
            finally:
                conn.close() # סגירה מבטיחה שה-DB לא יישאר נעול
                
        return response_data