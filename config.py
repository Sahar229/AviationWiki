import os
from dotenv import load_dotenv

load_dotenv()


class ServerConfig:
    """הגדרות שרת כלליות ואבטחה"""
    SECRET_KEY = os.getenv("SECRET_KEY")
    PORT = 5000
    HOST = '0.0.0.0'
    CERT_FILE = os.getenv("CERT_PATH")
    KEY_FILE = os.getenv("KEY_PATH")

class DBConfig:
    """ הגדרות תקשורת בין השרת הראשי לשרת בסיס הנתונים"""
    HOST1 = '0.0.0.0'
    HOST2= '127.0.0.1'
    PORT = 5002

class GameRules:
    """חוקי המשחק והחידון"""
    DEFAULT_MAX_PLAYERS = 4
    DEFAULT_NUM_QUESTIONS = 10
    MIN_PLAYERS = 2
    
    # זמנים (בשניות)
    QUESTION_TIMER = 15
    ROUND_TRANSITION_DELAY = 2
    GAME_START_DELAY = 2
    REFRESH_DELAY = 0.5
    
    # ניקוד
    BASE_POINTS = 100
    PENALTY_PER_OTHER_CORRECT = 5

class UserConfig:
    """הגדרות משתמשים והרשמה"""
    MIN_PASSWORD_LENGTH = 6

class APIConfig:
    """הגדרות שימוש בAPI"""
    API_KEY = os.getenv("GEMINI_API_KEY")