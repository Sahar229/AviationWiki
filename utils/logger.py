import logging
import sys

def setup_logger():
    """
    מגדיר ויוצר את הלוגר הראשי של המערכת.
    """
    # 1. יצירת האובייקט של הלוגר
    logger = logging.getLogger("QuizGame")
    logger.setLevel(logging.DEBUG) # מגדיר את הרמה המינימלית של הודעות שיוצגו

    # מניעת הדפסה כפולה אם הפונקציה נקראת פעמיים
    if logger.handlers:
        return logger

    # 2. הגדרת הפורמט של ההודעות (זמן - שם המודול - רמת ההודעה - ההודעה עצמה)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 3. יצירת "מטפל" שמדפיס לקונסול (מסך)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 4. אופציונלי: יצירת "מטפל" שכותב את הלוגים גם לקובץ טקסט
    file_handler = logging.FileHandler('server.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# יצירת המופע הגלובלי של הלוגר שכולם ישתמשו בו
logger = setup_logger()