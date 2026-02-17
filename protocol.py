import socket
import json

# גודל הכותרת המגדירה את אורך ההודעה
HEADER_LENGTH = 10

def send_message(sock, command, params=None):
    """
    פונקציה לשליחת הודעה לפי הפרוטוקול.
    מקבלת: סוקט, שם פקודה, ופרמטרים (מילון או רשימה).
    """
    if params is None:
        params = {}
    
    message_dict = {
        "command": command,
        "params": params
    }
    
    message_str = json.dumps(message_dict)
    message_bytes = message_str.encode('utf-8')
    
    header = str(len(message_bytes)).zfill(HEADER_LENGTH).encode('utf-8')
    
    try:
        sock.sendall(header + message_bytes)
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False


def receive_message(sock):
    """
    פונקציה לקבלת הודעה.
    דואגת לקרוא קודם את האורך ואז את כל המידע.
    מחזירה: (command, params) או (None, None) במקרה של שגיאה/ניתוק.
    """
    try:
        # 1. קריאת הכותרת (האורך)
        header = b""
        while len(header) < HEADER_LENGTH:
            packet = sock.recv(HEADER_LENGTH - len(header))
            if not packet:
                return None, None # הצד השני סגר את החיבור
            header += packet
        
        message_length = int(header.decode('utf-8'))
        
        # 2. קריאת המידע עצמו לפי האורך שהתקבל
        data = b""
        while len(data) < message_length:
            packet = sock.recv(message_length - len(data))
            if not packet:
                return None, None
            data += packet
            
        # 3. המרה חזרה מ-JSON
        message_dict = json.loads(data.decode('utf-8'))
        return message_dict["command"], message_dict["params"]
        
    except Exception as e:
        # במקרה של ניתוק או שגיאה
        return None, None