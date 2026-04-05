class ServerConfig:
    """הגדרות שרת כלליות ואבטחה"""
    SECRET_KEY = b'\xff}^\x06\x05/\x91\xb7\xb2\x86\xd3\xe0,e\xfe\xfb\x04\xb1\xec\n\xf1\\\x07Y'
    PORT = 5000
    HOST = '0.0.0.0'
    CERT_FILE = 'cert.pem'
    KEY_FILE = 'key.pem'

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
    
    # ניקוד
    BASE_POINTS = 100
    PENALTY_PER_OTHER_CORRECT = 5

class UserConfig:
    """הגדרות משתמשים והרשמה"""
    MIN_PASSWORD_LENGTH = 6