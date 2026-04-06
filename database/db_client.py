import socket
import ssl
from database.protocol import *
from config import DBConfig
from utils.logger import logger

class DatabaseClient:
    """
    מחלקה המייצגת לקוח שמתקשר מול שרת בסיס הנתונים.
    מיועדת לשימוש על ידי השרת הראשי  כדי להעביר בקשות בצורה מסודרת ונקייה.
    """
    def __init__(self, ip=DBConfig.HOST2, port=DBConfig.PORT):
        self._ip = ip
        self._port = port
        self._context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._context.check_hostname = False 
        self._context.verify_mode = ssl.CERT_NONE

    def send_request(self, command: str, params):
        """
        פונקציה השולחת בקשה לשרת הנתונים, ממתינה לתשובה, וסוגרת את החיבור.
        מחזירה מילון עם נתוני התשובה או כלום אם הייתה שגיאת התחברות.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            secure_sock = self._context.wrap_socket(sock, server_hostname=self._ip)
            secure_sock.connect((self._ip, self._port))
            
            ProtocolTools.send_message(secure_sock, command, params)
            cmd, response_data = ProtocolTools.receive_message(secure_sock)
            secure_sock.close()
            return response_data
        except Exception as e:
            logger.exception(f"|db_client.py| Database connection error")
            return None