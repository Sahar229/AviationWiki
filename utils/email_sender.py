import smtplib
import ssl
from email.message import EmailMessage
from utils.logger import logger


class EmailManager:
    """
    מחלקה האחראית על שליחת אימיילים מהמערכת.
    """
    def __init__(self, sender_email: str, app_password: str):
        # שומרים את פרטי ההתחברות כמשתני מחלקה
        self._sender_email = sender_email
        self._app_password = app_password
        self._smtp_server = 'smtp.gmail.com'
        self._smtp_port = 465

    def send_email(self, receiver_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """
        פונקציה לשליחת המייל בפועל.
        מקבלת אימייל נמען, נושא, תוכן, ופרמטר אופציונלי שקובע אם התוכן הוא HTML.
        מחזירה אמת אם השליחה הצליחה, ו-שקר אם נכשלה.
        """
        try:
            em = EmailMessage()
            em['From'] = self._sender_email
            em['To'] = receiver_email
            em['Subject'] = subject
            
            # הגדרת תוכן המייל (תמיכה בטקסט רגיל או HTML)
            if is_html:
                em.set_content(body, subtype='html')
            else:
                em.set_content(body)

            # יצירת חיבור מאובטח ושליחה
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self._smtp_server, self._smtp_port, context=context) as smtp:
                smtp.login(self._sender_email, self._app_password)
                smtp.send_message(em)
                
            logger.info(f"|email_utils.py| Successfully sent email to: {receiver_email}")
            return True
            
        except Exception as e:
            logger.exception(f"|email_utils.py| Failed to send email to {receiver_email}. Error: {str(e)}")
            return False