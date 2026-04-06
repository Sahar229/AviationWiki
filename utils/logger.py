import logging
import sys

def setup_logger():
    """
    מגדיר ויוצר את הלוגר הראשי של המערכת.
    """
    # יצירת האובייקט של הלוגר
    logger = logging.getLogger("QuizGame")
    logger.setLevel(logging.DEBUG) # מגדיר את הרמה המינימלית של הודעות שיוצגו
    
    if logger.handlers:
        return logger

    # הגדרות פורמט
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # לוגים לקונסול
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # כתיבת לוגים למסמך
    file_handler = logging.FileHandler('server.log', mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# יצירת המופע הגלובלי של הלוגר שכולם ישתמשו בו
logger = setup_logger()