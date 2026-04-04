import socket
import threading
from database.protocol import *
from database.db_manager import *
from config import DBConfig
from utils.logger import logger

class DatabaseServer:
    """
    מחלקה המייצגת את שרת בסיס הנתונים .
    מקשיבה לבקשות מלקוחות , מנתבת את הבקשות לבסיס נתונים עצמו, ומחזירה תשובה.
    """
    def __init__(self, ip=DBConfig.HOST2, port=DBConfig.PORT):
        self._ip = ip
        self._port = port
        self._db = DatabaseManager()

    def _process_login(self, client_socket: socket.socket, params) -> None:
        """
        פונקציה המעבדת בקשת התחברות.
        שולפת את הנתונים, מבצעת שאילתה מול בסיס הנתונים, ושולחת תשובה חזרה ללקוח.
        מחזירה: כלום. הפעולה שולחת את תוצאת הפעולה ישירות לסוקט.
        """
        response_data = {}
        try:
            email = params.get("email")
            password = params.get("password")
            
            user = self._db.login(email,password)
            
            if user:
                response_data = {"status": "ok", "user_id": user[0], "username": user[1]}           
            else:
                response_data = {"status": "fail", "error": "Incorrect Email or Password"}

        finally:
            ProtocolTools.send_message(client_socket, "LOGIN_RESPONSE", response_data)
    
    def _process_register(self, client_socket: socket.socket, params) -> None:
        """
        פונקציה המעבדת בקשת הרשמה.
        מפעילה את מתודת הרישום בבסיס הנתונים ומחזירה את התוצאה ללקוח.
        מחזירה: כלום. הפעולה שולחת את תוצאת הפעולה ישירות לסוקט.
        """
        response_data = {}
        try:
            username = params.get("username")
            email = params.get("email")
            password = params.get("password")
            
            response_data = self._db.register(username, email, password)
        finally:
          ProtocolTools.send_message(client_socket, "REGISTER_RESPONSE", response_data)

    def _process_update_stats(self, client_socket: socket.socket, params) -> None:
        """
        פונקציה המעבדת בקשה לעדכון סטטים.
        מפעילה את מתודת עדכון הסטטים בבסיס הנתונים ומחזירה את התוצאה ללקוח.
        מחזירה: כלום. הפעולה שולחת את תוצאת הפעולה ישירות לסוקט.
        """
        response_data = {}
        try:
            username = params.get("username")
            won = params.get("won", False)
            correct_count = params.get("correct_count",0)
        
            if username is None:
                response_data = {"status": "fail", "error": "Missing username"}
                logger.warning("Missing username")
            else:
                response_data = self._db.update_user_stats(username, won, correct_count)
                
        except Exception as e: # שיפור: תפיסת שגיאות ברמת השרת
            logger.error(f"Error in process_update_stats: {e}")
            response_data = {"status": "fail", "error": "Internal server error"}
        finally:
            ProtocolTools.send_message(client_socket, "UPDATE_STATS_RESPONSE", response_data)


    def _process_get_stats(self, client_socket: socket.socket, params) -> None:
        """
        פונקציה המקבלת בקשה לקבלת סטטים של משתמש.
        מקבלת מספר זיהוי של משתמש ומפעילה מתודת החזרת נתונים מבסיס הנתונים.
        מחזירה: שולחת ישירות לסוקט את הסטטים של המשתמש
        """
        response_data = {}
        try:
            user_id = params.get("user_id")
            if user_id is None:
                response_data = {"status": "fail", "error": "Missing user_id"}
            else:
                stats = self._db.get_user_stats(user_id)
                if stats:
                    response_data = {"status": "ok", "stats": stats}
                else:
                    response_data = {"status": "fail", "error": "User not found"}
                    logger.warning("User not found")
                    
        except Exception as e:
            logger.error(f"Error in process_get_stats: {e}")
            response_data = {"status": "fail", "error": "Internal server error"}
        finally:
            ProtocolTools.send_message(client_socket, "GET_STATS_RESPONSE", response_data)
    


    def handle_client(self, client_socket: socket.socket, client_address) -> None:
        """
        פונקציה הרצה בתהליכון נפרד עבור כל לקוח שמתחבר.
        מאזינה לבקשות נכנסות, מנתבת אותן לפונקציה המתאימה, ובסיום דואגת לסגור את החיבור.
        מחזירה: כלום.
        """
        try:
            while True:
                #קבלת נתונים
                command, params = ProtocolTools.receive_message(client_socket)
                if not command:
                    break
        
                logger.info(f"Received command: {command} from {client_address}")

                #בדיקת פקודה ושליחה לפעולה המתאימה
                if command == "LOGIN_REQUEST":
                    self._process_login(client_socket, params)
        
                elif command == "REGISTER_REQUEST":
                    self._process_register(client_socket, params) 

                elif command == "UPDATE_STATS_REQUEST":
                    self._process_update_stats(client_socket, params)
                
                elif command == "GET_STATS_REQUEST":
                    self._process_get_stats(client_socket, params)

        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def start_server(self) -> None:
        """
        פונקציית ההפעלה של השרת.
        פותחת סוקט האזנה ומקבלת חיבורים חדשים בלולאה אינסופית. כל חיבור חדש נפתח ב-Thread משלו.
        מחזירה: כלום.
        """
        #מעלה לאוויר את השרת
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self._ip, self._port))
        server.listen(5)
        
        logger.info(f"[*] Database Server listening on port {self._port}...")
        
        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()