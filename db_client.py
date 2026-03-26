import socket
from protocol import *

class DatabaseClient:
    """
    מחלקה המייצגת לקוח שמתקשר מול שרת בסיס הנתונים.
    מיועדת לשימוש על ידי השרת הראשי  כדי להעביר בקשות בצורה מסודרת ונקייה.
    """
    def __init__(self, ip='127.0.0.1', port=5002):
        self.ip = ip
        self.port = port

    def send_request(self, command: str, params):
        """
        פונקציה השולחת בקשה לשרת הנתונים, ממתינה לתשובה, וסוגרת את החיבור.
        מחזירה מילון עם נתוני התשובה או כלום אם הייתה שגיאת התחברות.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.ip, self.port))
            
            ProtocolTools.send_message(sock, command, params)
            cmd, response_data = ProtocolTools.receive_message(sock)
            sock.close()
            return response_data
        except Exception as e:
            print(f"Database connection error: {e}")
            return None