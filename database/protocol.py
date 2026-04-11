import socket
import json
import base64
from utils.logger import logger
from utils.crypto_utils import NetworkCipher
from config import DBConfig

# גודל הכותרת המגדירה את אורך ההודעה
class ProtocolTools:
    """
    מחלקה הקובעת ומציבה את כללי התקשורת בין השרת הראשי לבין שרת מבנה הנתונים
    """

    @staticmethod
    def _generate_header(message_bytes):
        """
        יצירת הדר מתאים להודעה לפי הפרוטוקול
        """
        return str(len(message_bytes)).zfill(DBConfig.HEADER_LENGTH).encode('utf-8')
    
    @staticmethod
    def _build_received_message(sock: socket.socket):
        """
        תהליך קבלת ובניית הודעה
        """
        header = b""
        try:
            while len(header) < DBConfig.HEADER_LENGTH:
                packet = sock.recv(DBConfig.HEADER_LENGTH - len(header))
                if not packet:
                    return None # הצד השני סגר את החיבור
                header += packet
            
            message_length = int(header.decode('utf-8'))
            
            # קריאת המידע עצמו לפי האורך שהתקבל
            data = b""
            while len(data) < message_length:
                packet = sock.recv(message_length - len(data))
                if not packet:
                    return None
                data += packet
            return data
        except Exception as e:
            logger.exception(f"|protocol.py| Error building message")
            return None

    @classmethod    
    def send_message(cls, sock: socket.socket, command: str, params = None) -> bool:
        """
        פונקציה לשליחת הודעה של לחיצת יד
        מקבלת סוקט פעיל, שם פקודה, ופרמטרים נלווים.
        מחזירה אמת אם השליחה הצליחה, ושקר במקרה של שגיאה.
        """
        if params is None:
            params = {}
        
        message_dict = {
            "command": command,
            "params": params
        }
        
        #הכנת גייסון
        message_str = json.dumps(message_dict)
        message_bytes = message_str.encode('utf-8')
        
        #הכנת הדר
        header = ProtocolTools._generate_header(message_bytes)
        
        #שליחה
        try:
            sock.sendall(header + message_bytes)
            return True
        except Exception as e:
            logger.exception(f"|protocol.py| Error sending message")
            return False
        

    @classmethod
    def send_encrypted_message(cls, sock : socket.socket, command : str, cipher: NetworkCipher, params = None) -> bool:
        """
        פונקציה לשליחת הודעה מוצפנת לפי הפרוטוקול
        מקבלת סוקט פעיל, שם פקודה, פרמטרים נלווים ומפתח משותף.
        מחזירה אמת אם השליחה הצליחה, ושקר במקרה של שגיאה.
        """
        message_dict = {"command": command, "params": params}
        json_data = json.dumps(message_dict)
        
        # הצפנה
        ciphertext, nonce, tag = cipher.aes_encrypt(json_data)
        
        # אריזה של הכל ב-JSON אחד (מקודד ב-base64 כדי שיעבור בטקסט)
        payload = {
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8')
        }
        
        final_data = json.dumps(payload).encode('utf-8')
        header = ProtocolTools._generate_header(final_data)
        try:
            sock.sendall(header + final_data)
            return True
        except Exception as e:
            logger.exception(f"|protocol.py| Error sending an encrypted message")
            return False


    @classmethod
    def receive_message(cls, sock: socket.socket):
        """
        פונקציה לקבלת הודעה של לחיצת היד.
        קוראת את הכותרת (כדי לדעת את אורך ההודעה) ואז את המידע המלא, וממירה מגייסון.
        מחזירה טאפל של (פקודה, פרמטרים). במקרה של שגיאה או ניתוק, מחזירה כלום
        """
        try:
            data = ProtocolTools._build_received_message(sock)
                
            # המרה מגייסון
            if not data:
                return None, None
            message_dict = json.loads(data.decode('utf-8'))
            return message_dict["command"], message_dict["params"]
            
        except Exception as e:
            logger.exception("|protocol.py| Error receiving a message")
            return None, None
        

    @classmethod
    def receive_encrypted_message(cls, sock : socket.socket, cipher: NetworkCipher):
        """
        פונקציה לקבלת הודעה מוצפנת לפי הפרוטוקול
        קוראת את הכותרת (כדי לדעת את אורך ההודעה) ואז את המידע המלא, וממירה מגייסון.
        מחזירה טאפל של (פקודה, פרמטרים). במקרה של שגיאה או ניתוק, מחזירה כלום
        """
        try:
            data = ProtocolTools._build_received_message(sock)

            if not data:
                return None, None
            payload = json.loads(data.decode('utf-8'))
            ciphertext = base64.b64decode(payload['ciphertext'])
            nonce = base64.b64decode(payload['nonce'])
            tag = base64.b64decode(payload['tag'])
            
            decrypted_json = cipher.aes_decrypt(ciphertext, nonce, tag)
            message = json.loads(decrypted_json)
            return message.get("command"), message.get("params")
        except Exception as e:
            logger.exception("|protocol.py| Error receiving an encrypted message")
            return None, None