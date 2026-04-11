import socket
import ssl
from database.protocol import *
from utils.crypto_utils import NetworkCipher
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
            
            #התחלת לחיצת יד עם השרת
            dh, my_pub_key = NetworkCipher.generate_dh_keys()

            ProtocolTools.send_message(secure_sock, "DH_HANDSHAKE", {"pub_key": my_pub_key})
            cmd, params1 = ProtocolTools.receive_message(secure_sock)
            if cmd == "DH_HANDSHAKE_RESPONSE":
                server_pub_key = params1["pub_key"]
                
            shared_key = NetworkCipher.compute_shared_key(dh, server_pub_key)
            cipher = NetworkCipher(shared_key) 

            logger.info(f"|db_client.py| completed handshake")

            #שליחת הודעה לאחר לחיצת היד
            ProtocolTools.send_encrypted_message(secure_sock, command, cipher, params)
            cmd, response_data = ProtocolTools.receive_encrypted_message(secure_sock, cipher)

            secure_sock.close()
            return response_data
        
        except Exception as e:
            logger.exception(f"|db_client.py| Database connection error")
            return None
        