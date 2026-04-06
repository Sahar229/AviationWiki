import sqlite3
import threading
from utils.logger import logger

class DatabaseManager:
    """
    מחלקה לניהול בסיס הנתונים
    משתמשת במנגנון נעילה כדי להבטיח עבודה בטוחה בסביבה מרובת תהליכונים
    """
    def __init__(self, db_name="users.db"):
        self._db_name = db_name
        self._lock = threading.Lock()
        
        #יצירת מסד נתונים
        with self._lock:
            conn = sqlite3.connect(self._db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    games_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    total_correct_answers INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
            conn.close()
        logger.info("|db_manager.py| [*] Database ready.")

    def login(self, email: str, password: str):
        """
        פונקציה לבדיקת התחברות משתמש.
        מחפשת במסד הנתונים משתמש עם האימייל והסיסמה שסופקו.
        מחזירה טאפל המכיל את אם נמצאה התאמה, או כלום אם לא.
        """
        user = None

        #ביצוע שאילתה
        with self._lock:
            conn = sqlite3.connect(self._db_name)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id, username FROM users WHERE email=? AND password=?", 
                               (email, password))
                user = cursor.fetchone()
            except Exception as e:
                logger.exception("|db_manager.py| Error in login")
            finally:
                conn.close()
        return user

    def register(self, username: str, email: str, password: str):
        """
        פונקציה לרישום משתמש חדש לבסיס הנתונים.
        מבצעת שמירה של הנתונים ומוודאת שאין כפילויות.
        מחזירה מילון עם מפתח 'סטטוס' והודעת שגיאה במקרה הצורך.
        """
        response_data = {}
        
        with self._lock:
            conn = sqlite3.connect(self._db_name) # פתיחה בתוך הפונקציה
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                               (username, email, password))
                conn.commit()
                response_data = {"status": "ok"}
                logger.info(f"|db_manager.py| Created new user: {username}")

            #בדיקת שגיאות
            except sqlite3.IntegrityError as e:
                error_message = str(e).lower()
                if "username" in error_message:
                    response_data = {"status": "fail", "error": "Username Already Exists"}
                    logger.warning(f"|db_manager.py| Username {username} Already Exists")
                elif "email" in error_message:
                    response_data = {"status": "fail", "error": "Email Already Exists"}
                    logger.warning(f"|db_manager.py| Email {email} Already Exists")
                else:
                    response_data = {"status": "fail", "error": "Username or Email Already Exists"}
                    logger.warning("|db_manager.py| Username or Email Already Existss")
            except Exception as e:
                response_data = {"status": "fail", "error": f"General error: {e}"}
                logger.exception("|db_manager.py| Error in register")
            finally:
                conn.close()
                
        return response_data
    
    def update_user_stats(self, username : str , won : bool , correct_count :int):
        """
        מעדכנת את הסטטיסטיקות של המשתמש בסיום משחק.
        won: בוליאני (אמת אם ניצח, שקר אם לא)
        correct_count: מספר התשובות הנכונות בחידון הספציפי הזה
        """
        with self._lock:
            conn = sqlite3.connect(self._db_name) # פתיחה בתוך הפונקציה
            cursor = conn.cursor()

            #הכנסת נתונים
            try:
                win_increment = 1 if won else 0
                cursor.execute('''
                    UPDATE users 
                    SET wins = wins + ?, 
                        games_played = games_played + 1, 
                        total_correct_answers = total_correct_answers + ?
                    WHERE username = ?
                ''', (win_increment, correct_count, username))
                conn.commit()
                return {"status": "ok"}
            except Exception as e:
                logger.exception("|db_manager.py| Error updating stats")
                return {"status": "fail", "error": str(e)}
            finally:
                conn.close()

    def get_user_stats(self, user_id: int):
        """
        פונקציה המקבלת מספר זיהוי של משתמש מסוים
        מחזירה מילון עם הנתונים או כלום אם המשתמש לא נמצא.
        """
        stats = None
        with self._lock:
            conn = sqlite3.connect(self._db_name)
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT wins, games_played, total_correct_answers 
                    FROM users 
                    WHERE id=?
                """, (user_id,))
                row = cursor.fetchone()

                #סידור במילון
                if row:
                    stats = {
                        "wins": row[0],
                        "games_played": row[1],
                        "total_correct_answers": row[2]
                    }
            except Exception as e:
                logger.exception(f"|db_manager.py| Error fetching stats for user {user_id}")
            finally:
                conn.close()
        return stats
    