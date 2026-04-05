import socket
import json
from utils.logger import logger

# גודל הכותרת המגדירה את אורך ההודעה
class ProtocolTools:
    """
    מחלקה הקובעת ומציבה את כללי התקשורת בין השרת הראשי לבין שרת מבנה הנתונים
    """
    HEADER_LENGTH = 10

    @classmethod    
    def send_message(cls, sock: socket.socket, command: str, params = None) -> bool:
        """
        פונקציה לשליחת הודעה לפי הפרוטוקול.
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
        header = str(len(message_bytes)).zfill(cls.HEADER_LENGTH).encode('utf-8')
        
        #שליחה
        try:
            sock.sendall(header + message_bytes)
            return True
        except Exception as e:
            logger.exception(f"|protocol.py| Error sending message")
            return False

    @classmethod
    def receive_message(cls, sock: socket.socket):
        """
        פונקציה לקבלת הודעה.
        קוראת את הכותרת (כדי לדעת את אורך ההודעה) ואז את המידע המלא, וממירה מגייסון.
        מחזירה טאפל של (פקודה, פרמטרים). במקרה של שגיאה או ניתוק, מחזירה כלום
        """
        try:
            # קריאת ההדר
            header = b""
            while len(header) < cls.HEADER_LENGTH:
                packet = sock.recv(cls.HEADER_LENGTH - len(header))
                if not packet:
                    return None, None # הצד השני סגר את החיבור
                header += packet
            
            message_length = int(header.decode('utf-8'))
            
            # קריאת המידע עצמו לפי האורך שהתקבל
            data = b""
            while len(data) < message_length:
                packet = sock.recv(message_length - len(data))
                if not packet:
                    return None, None
                data += packet
                
            # המרה מגייסון
            message_dict = json.loads(data.decode('utf-8'))
            return message_dict["command"], message_dict["params"]
            
        except Exception as e:
            logger.exception("|protocol.py| Error receiving a message")
            return None, None